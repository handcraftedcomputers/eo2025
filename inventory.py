##  Inventory file, EO2025

inventory = (
    [
        # Host name, local data
        ('host1', {'ssh_hostname': 'host1.example.com.' }),
        ('host2', {'ssh_hostname': 'host2.example.com.' }),
        ('host3', {'ssh_hostname': 'host3.example.com.' }),
    ],
    # Group data
    {
        'ssh_user':             'ansible',
        'ssh_key':              '/home/XXXXX/.ssh/ansible',
        'ssh_known_hosts_file': '/etc/ssh/ssh_known_hosts',
        'acme_path':            '/home/XXXXX/.acme.sh',
        'acme_domains':         'example.com,goodcorp.org',
        # https://github.com/paramiko/paramiko/issues/1984
        ##  'ssh_paramiko_connect_kwargs': {
        ##      'disabled_algorithms': {
        ##          'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']
        ##      }
        ##  },
    },
)
