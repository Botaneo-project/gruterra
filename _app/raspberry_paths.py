"""Shell-safe remote paths. No network access or filesystem mutation."""
import re
import shlex


def validate_home(config):
    home=config.get('installation_home')
    if home is None:
        return
    # Deliberately limit paths to a portable subset usable by SSH and SCP/SFTP.
    if not isinstance(home,str) or not re.fullmatch(r'/[A-Za-z0-9_.\-/]+',home):
        raise ValueError('Raspberry installation_home must be an absolute POSIX path without spaces')
    if '..' in home or any(part in ('', '.', '..') for part in home.split('/')[1:]) or home == '/':
        raise ValueError('Invalid Raspberry installation_home')


def remote_command(config, script, *arguments):
    validate_home(config)
    if script not in ('sync_export.py','backup_manifest.py','weather_backup.py'):
        raise ValueError('Unknown Raspberry utility')
    home=config.get('installation_home')
    path=shlex.quote(home+'/collector/'+script) if home else '~/botaneo/collector/'+script
    return 'python3 '+path+''.join(' '+shlex.quote(arg) for arg in arguments)


def remote_backup(config, kind, name):
    validate_home(config)
    if kind not in ('daily','weather') or not re.fullmatch(r'(?:collector|weather)-\d{4}-\d{2}-\d{2}\.sqlite3',name):
        raise ValueError('Invalid Raspberry backup path')
    return config.get('installation_home','botaneo')+'/backups/'+kind+'/'+name
