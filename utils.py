##  pyinfra utility methods.

from io import BytesIO
from pyinfra.api import operation, StringCommand, QuoteString
from pyinfra import facts
from pyinfra.operations import systemd, runit, server
from pyinfra.api.exceptions import OperationError
from pyinfra import host


##  Simple operation wrapper around "cp" command.
@operation()
def cp(source: str, dest: str):
    yield StringCommand("cp", "-p", QuoteString(source), QuoteString(dest))


# We die like real Unix men!
@operation()
def mv(source: str, dest: str):
    yield StringCommand("mv", QuoteString(source), QuoteString(dest))


##  Return a BytesIO object containing the concatenated contents of all filenames supplied, in order.
def concat_files(*filenames: str) -> BytesIO:
    s = BytesIO()
    for fname in filenames:
        with open(fname, 'rb') as f:
            s.write(f.read())
    s.seek(0, 0)        # Please be kind, rewind.
    return s


##  Reload system service, by hook or by crook.
@operation()
def reload_service(service_name: str) -> None:
    # Check for runit managed service.
    svdir = '/etc/service'      # Thank you, Debian.
    if host.get_fact(facts.files.Directory, svdir):
        runit_svc = host.get_fact(facts.runit.RunitManaged, svdir=svdir)
        if runit_svc and service_name in runit_svc:
            # THIS IS NOT SIGUSR1 - lighttpd needs special love!
            if service_name == 'lighttpd':
                # "name" no workee.
                yield from server.shell._inner(commands='sv 1 lighttpd')
            else:
                yield from runit.service._inner(service_name, running=None, reloaded=True)
            return

    # Check for systemd managed service.  Still needs a systemd guard.
    systemd_svc = host.get_fact(facts.systemd.SystemdStatus)
    if systemd_svc and '%s.service' % service_name in systemd_svc:
        # running=None means leave service state as found
        yield from systemd.service._inner(service_name, running=None, reloaded=True)
        return

    # Bad juju if we got to here ...
    raise OperationError('no matching service handler for %s' % service_name)
