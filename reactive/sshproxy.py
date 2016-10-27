from charmhelpers.core.hookenv import (
    action_fail,
    action_get,
    action_set,
    config,
    log,
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
        log("Running command: " + cmd)
        output, err = charms.sshproxy._run(cmd)
        log("Ran command: " + cmd)
        if len(err):
            log("Action failed")
            action_fail("Command '{}' returned error code {}".format(cmd, err))
        else:
            log("Action succeeded: " + output)
            action_set({'output': output})
    except subprocess.CalledProcessError as e:
        log("Action failed.")
        action_fail('Command failed: %s (%s)' %
                    (' '.join(e.cmd), str(e.output)))
    finally:
        remove_state('actions.run')
    log("Action done")
