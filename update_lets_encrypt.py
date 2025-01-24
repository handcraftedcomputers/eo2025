##  pyinfra deploy script to push Let's Encrypt certificates where they're required
##  and reload services that depend on them.
##  services covered:
##    postfix:   p3
##    lighttpd:  p1, p2, p3
##  --data acme_path - path to acme certs, --data acme_domains - comma separated list of domains.

from os import path
from pyinfra import host, logger, config
from pyinfra.facts import files as fact
from pyinfra.operations import files
from utils import mv, concat_files, reload_service
import hashlib


##  Update remote certificate *only* if required, atomically, race-free, and potentially
##  archived.
##  returns True if cert was updated (indicating a subsystem reload required), False otherwise.

def update_cert(
        subsystem: str,     # subsystem - e.g. postfix, lighttpd
        cert: file,         # new combined cert
        cert_dir: str,      # path to subsystem's cert directory
        domain: str,        # name of cert's domain
        owner: str,         # owner of cert
        group: str,         # group owner of cert
        file_mode: str,     # file permissions
        archive: bool = True    # archive old cert
) -> bool:
    # If cert_dir doesn't exist, abort.
    if host.get_fact(fact.Directory, cert_dir) is None:
        return False
    # If cert doesn't exist, abort (None if doesn't exist, False if not a file)
    cert_path = path.join(cert_dir, domain + '.pem')
    if not host.get_fact(fact.File, cert_path):
        return False
    # If sha1's match, no update required.
    remote_sha1 = host.get_fact(fact.Sha1File, cert_path)
    if remote_sha1 is None:     # Hmmm
        logger.warning('%s: %s: unable to obtain hash of %s', host.name, subsystem, cert_path)
        return False
    local_sha1 = hashlib.sha1()
    local_sha1.update(cert.read())
    local_sha1 = local_sha1.hexdigest()
    if remote_sha1 == local_sha1:
        return False
    ##  All checks passed, cert is ripe for upgrading in atomic (nuclear?) fashion.
    # Upload cert to temporary (sha1 hash) file name.
    files.put(name='upload %s cert' % subsystem, src=cert, dest=path.join(cert_dir, local_sha1 + '.pem'),
            user=owner, group=group, mode=file_mode)
    if archive:
        # Create archive directory if required.
        if host.get_fact(fact.Directory, path.join(cert_dir, 'old_certs')) is None:
            files.directory(path.join(cert_dir, 'old_certs'), user='root', group='root', mode='700')
        # Create backup of current cert (as hash) if it doesn't already exist.
        backup_pem = path.join(cert_dir, 'old_certs', remote_sha1 + '.pem')
        if host.get_fact(fact.File, backup_pem) is None:
            files.link(path=backup_pem, target=cert_path, symbolic=False)
    # Move new temporary named cert into place.
    mv(name='move %s cert into place' % subsystem, source=path.join(cert_dir, local_sha1 + '.pem'),
            dest=cert_path)

    return True


def deploy_certs() -> None:
    config.SUDO = True
    reload_svc = set()
    # Loop over each supplied domain
    for domain in host.data.acme_domains.split(','):
        acme_path = path.join(host.data.acme_path, domain)
        # Create combined cert (key + full chain).
        file_list = [path.join(acme_path, fname) for fname in [domain + '.key', 'fullchain.cer']]
        key_cert = concat_files(*file_list)
        # Update postfix
        if update_cert('postfix', key_cert, '/etc/postfix/certs', domain, 'root', 'postfix', '400'):
            reload_svc.add('postfix')
        key_cert.seek(0, 0)     # Rewind
        # Update lighttpd
        if update_cert('lighttpd', key_cert, '/etc/lighttpd/certs', domain, 'root', 'www-data', '440'):
            reload_svc.add('lighttpd')
        key_cert.seek(0, 0)     # Rewind
        # nginx to go here.
    # Reload services as/if required.
    for svc in reload_svc:
        reload_service(name='reloading %s' % svc, service_name=svc)


deploy_certs()

