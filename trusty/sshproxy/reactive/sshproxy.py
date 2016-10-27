from charmhelpers.core.hookenv import config
from charms.reactive import (
    when,
    when_not,
    set_state,
    remove_state,
)
import paramiko
from subprocess import (
    Popen,
    CalledProcessError,
    PIPE,
)


@when('config.changed')
def config_changed():
    if 1:
        set_state('sshproxy.configured')
    else:
        remove_state('sshproxy.configured')


@when_not('sshproxy.installed')
def install_sshproxy():
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_state('sshproxy.installed')


@when('action.run')
def _run(cmd, env=None):
    """ Run a command, either on the local machine or remotely via SSH. """
    if isinstance(cmd, str):
        cmd = cmd.split() if ' ' in cmd else [cmd]

    cfg = config()
    if all(k in cfg for k in ['pass', 'vpe-router', 'user']):
        router = cfg['vpe-router']
        user = cfg['user']
        passwd = cfg['pass']

        if router and user and passwd:
            return ssh(cmd, router, user, passwd)

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
    return (''.join(stdout), ''.join(stderr))


def ssh(cmd, host, user, password=None):
    ''' Suddenly this project needs to SSH to something. So we replicate what
        _run was doing with subprocess using the Paramiko library. This is
        temporary until this charm /is/ the VPE Router '''

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
    return (''.join(stdout), ''.join(stderr))
