from charmhelpers.core.hookenv import (
    config,
)
import io
import paramiko

from subprocess import (
    Popen,
    CalledProcessError,
    PIPE,
)


def _run(cmd, env=None):
    """ Run a command, either on the local machine or remotely via SSH. """
    if isinstance(cmd, str):
        cmd = cmd.split() if ' ' in cmd else [cmd]
    cfg = config()
    if all(k in cfg for k in ['ssh-hostname', 'ssh-username',
                              'ssh-password', 'ssh-private-key']):
        host = cfg['ssh-hostname']
        user = cfg['ssh-username']
        passwd = cfg['ssh-password']
        key = cfg['ssh-private-key']

        if host and user and (passwd or key):
            return ssh(cmd, host, user, passwd, key)

    p = Popen(cmd,
              env=env,
              stdout=PIPE,
              stderr=PIPE)
    stdout, stderr = p.communicate()
    retcode = p.poll()
    if retcode > 0:
        raise CalledProcessError(returncode=retcode,
                                 cmd=cmd,
                                 output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip())


def ssh(cmd, host, user, password=None, key=None):
    """ Run an arbitrary command over SSH. """

    cmds = ' '.join(cmd)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pkey = None
    if key:
        f = io.StringIO(key)
        pkey = paramiko.RSAKey.from_private_key(f)

    client.connect(host, port=22, username=user, password=password, pkey=pkey)

    stdin, stdout, stderr = client.exec_command(cmds, get_pty=True)
    retcode = stdout.channel.recv_exit_status()
    client.close()  # @TODO re-use connections
    if retcode > 0:
        output = stderr.read().strip()
        raise CalledProcessError(returncode=retcode, cmd=cmd,
                                 output=output)
    return (
        stdout.read().decode('utf-8').strip(),
        stderr.read().decode('utf-8').strip()
    )
