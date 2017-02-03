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
        cmd = cmd.split(' ') if ' ' in cmd else [cmd]

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
              shell=True,
              stdout=PIPE,
              stderr=PIPE)
    stdout, stderr = p.communicate()
    retcode = p.poll()
    if retcode > 0:
        raise CalledProcessError(returncode=retcode,
                                 cmd=cmd,
                                 output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip())


def get_ssh_client(host, user, password=None, key=None):
    """Return a connected Paramiko ssh object"""

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pkey = None
    if key:
        f = io.StringIO(key)
        pkey = paramiko.RSAKey.from_private_key(f)

    ###########################################################################
    # There is a bug in some versions of OpenSSH 4.3 (CentOS/RHEL 5) where    #
    # the server may not send the SSH_MSG_USERAUTH_BANNER message except when #
    # responding to an auth_none request. For example, paramiko will attempt  #
    # to use password authentication when a password is set, but the server   #
    # could deny that, instead requesting keyboard-interactive. The hack to   #
    # workaround this is to attempt a reconnect, which will receive the right #
    # banner, and authentication can proceed. See the following for more info #
    # https://github.com/paramiko/paramiko/issues/432                         #
    # https://github.com/paramiko/paramiko/pull/438                           #
    ###########################################################################

    try:
        client.connect(host, port=22, username=user,
                       password=password, pkey=pkey)
    except paramiko.ssh_exception.SSHException as e:
        if 'Error reading SSH protocol banner' == str(e):
            # Once more, with feeling
            client.connect(host, port=22, username=user,
                           password=password, pkey=pkey)
            pass
        else:
            raise paramiko.ssh_exception.SSHException(e)

    return client


def sftp(local_file, remote_file, host, user, password=None, key=None):
    """Copy a local file to a remote host"""
    client = get_ssh_client(host, user, password, key)

    # Create an sftp connection from the underlying transport
    sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    sftp.put(local_file, remote_file)
    client.close()


def ssh(cmd, host, user, password=None, key=None):
    """ Run an arbitrary command over SSH. """
    client = get_ssh_client(host, user, password, key)

    cmds = ' '.join(cmd)
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
