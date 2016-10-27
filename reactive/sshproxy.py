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
def config_changed():
    # cfg = config()
    if 1:
        set_state('sshproxy.configured')
    else:
        remove_state('sshproxy.configured')


@when('actions.run')
def run_command():
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
