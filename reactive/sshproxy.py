from charmhelpers.core.hookenv import (
    action_fail,
    action_get,
    action_set,
    config,
)
from charms.reactive import (
    remove_state,
    set_state,
    when,
)
import charms.sshproxy
import subprocess


@when('config.changed')
def ssh_configured():
    """ Checks to see if the charm is configured with SSH credentials. If so,
    set a state flag that can be used to execute ssh-only actions.

    For example:

    @when('sshproxy.configured')
    def run_remote_command(cmd):
        ...

    @when_not('sshproxy.configured')
    def run_local_command(cmd):
        ...
    """
    cfg = config()
    if all(k in cfg for k in ['ssh-hostname', 'ssh-username', 'ssh-password']):
        set_state('sshproxy.configured')
    else:
        remove_state('sshproxy.configured')


@when('actions.run')
def run_command():
    """
    Run an arbitrary command, either locally or over SSH with the configured
    credentials.
    """
    try:
        cmd = action_get('command')
        output, err = charms.sshproxy._run(cmd)
        if len(err):
            action_fail("Command '{}' returned error code {}".format(cmd, err))
        else:
            action_set({'output': output})
    except subprocess.CalledProcessError as e:
        action_fail('Command failed: %s (%s)' %
                    (' '.join(e.cmd), str(e.output)))
    finally:
        remove_state('actions.run')
