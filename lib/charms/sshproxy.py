from charmhelpers.core.hookenv import (
    config,
    log,
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
    log("Running command: {}".format(cmd))
    cfg = config()
    log("Checking configuration: %s" % cfg)
    if all(k in cfg for k in ['ssh-hostname', 'ssh-username', 'ssh-password']):
        host = cfg['ssh-hostname']
        user = cfg['ssh-username']
        passwd = cfg['ssh-password']

        if host and user and passwd:
            log("Calling SSH")
            return ssh(cmd, host, user, passwd)

    log("Calling local process")
    p = Popen(cmd,
              env=env,
              stdout=PIPE,
              stderr=PIPE)
    log("Communicating with process")
    stdout, stderr = p.communicate()
    log("Polling return code")
    retcode = p.poll()
    if retcode > 0:
        log("Raising exception")
        raise CalledProcessError(returncode=retcode,
                                 cmd=cmd,
                                 output=stderr.decode("utf-8").strip())
    log("Returning output/err")
    return (stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip())


def ssh(cmd, host, user, password=None):
    ''' Suddenly this project needs to SSH to something. So we replicate what
        _run was doing with subprocess using the Paramiko library. This is
        temporary until this charm /is/ the VPE Router '''

    cmds = ' '.join(cmd)
    log("Running command(s): " + cmds)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log("Connecting to %s" % host)
    client.connect(host, port=22, username=user, password=password)

    stdin, stdout, stderr = client.exec_command(cmds)
    retcode = stdout.channel.recv_exit_status()
    client.close()  # @TODO re-use connections
    log("Checking output")
    if retcode > 0:
        output = stderr.read().strip()
        raise CalledProcessError(returncode=retcode, cmd=cmd,
                                 output=output)
    return (''.join(stdout), ''.join(stderr))
