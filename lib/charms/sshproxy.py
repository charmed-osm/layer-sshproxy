from charmhelpers.core.hookenv import (
    config,
)
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
    if all(k in cfg for k in ['ssh-hostname', 'ssh-username', 'ssh-password']):
        host = cfg['ssh-hostname']
        user = cfg['ssh-username']
        passwd = cfg['ssh-password']

        if host and user and passwd:
            return ssh(cmd, host, user, passwd)

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


def ssh(cmd, host, user, password=None):
    """ Run an arbitrary command over SSH. """

    cmds = ' '.join(cmd)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=22, username=user, password=password)

    stdin, stdout, stderr = client.exec_command(cmds)
    retcode = stdout.channel.recv_exit_status()
    client.close()  # @TODO re-use connections
    if retcode > 0:
        output = stderr.read().strip()
        raise CalledProcessError(returncode=retcode, cmd=cmd,
                                 output=output)
    return (stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip())
