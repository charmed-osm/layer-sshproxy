
# Overview

This [Juju] layer is intended to ease the development of charms that need
to execute commands over SSH, such as [proxy charms].

# Security

The initial version of this charm exposed configuration values for `ssh-password` and `ssh-private-key`; this approach was flawed. These fields are deprecated and only there for backwards compatibility.

On install, the layer will generate a new keypair, and expose the public key via the `ssh-public-key` [action].

## Workflow
1. Deploy charm that includes sshproxy layer
2. Set `ssh-hostname` and `ssh-username`
3. Call the `ssh-public-key` action and add it's `pubkey` output to the user and machine specified by `ssh-username` and `ssh-hostname`. This can be done via `cloud-init`.
4. Invoke `verify-ssh-credentials` action to verify the unit can connect to the `ssh-hostname` and authenticate.

# Actions

The following actions are available to use:

- generate-ssh-key: Generate a ssh keypair. This is done automatically and should only be called if you wish to re-generate the keypair used by your charm.
- verify-ssh-credentials: Verify authentication against the specified `ssh-hostname` using either `ssh-password` or public-key authentication.
- get-ssh-public-key: Returns the public key of your charm.
- run: Run a command against the remote machine.

# Integration

After you've [created your charm], open `interfaces.yaml` and add
`layer:sshproxy` to the includes stanza, as shown below:
```
includes: ['layer:basic', 'layer:sshproxy']
```

## Reactive states

This layer will set the following states:

- `sshproxy.configured` This state is set when SSH credentials have been supplied to the charm.


## Example
In `reactive/mycharm.py`, you can add logic to execute commands over SSH. This
example is run via a `start` action, and starts a service running on a remote
host.
```python
import charms.sshproxy


@when('sshproxy.configured')
@when('actions.start')
def start():
    """ Execute's the command, via the start action` using the
    configured SSH credentials
    """
    try:
        # Runs the command via ssh proxy
        (stdout, stderr) = sshproxy.run("service myservice start")
        if len(stderr) == 0:
            action_fail(
                'Restarting service myservice failed {}'.format(stderr)
            )
        else:
            action_set({'success': get_ssh_public_key()})
    except Exception as e:
        action_fail('Command failed: %s (%s)' %
                    (' '.join(e.cmd), str(e.output)))
    finally:
        clear_flag('actions.get-ssh-public-key')
```

You can find more examples of proxy charm usage in the [OSM Hackfest](https://github.com/AdamIsrael/osm-hackfest) repository.

## Actions
This layer includes a built-in `run` action useful for debugging or running arbitrary commands:

```
$ juju run-action mycharm/0 run command=hostname
Action queued with id: 014b72f3-bc02-4ecb-8d38-72bce03bbb63

$ juju show-action-output 014b72f3-bc02-4ecb-8d38-72bce03bbb63
results:
  output: juju-66a5f3-11
status: completed
timing:
  completed: 2016-10-27 19:53:49 +0000 UTC
  enqueued: 2016-10-27 19:53:44 +0000 UTC
  started: 2016-10-27 19:53:48 +0000 UTC

```
## Known Limitations and Issues
## Caveats
### Returning data via `action-set` can fail with "Argument list too long"

Because the `action_set` method is a wrapper to the bash `action-set` command, we must abide by ARG_MAX. If the data being set is too long, the command will fail.

This can happen if you're running a command that generates a lot of output to stdout. In this case, you can either modify your command to pipe stdout to /dev/null, or if you need the output, capture it to a file and return the file location via action.

```
action-set output.name="/path/to/output.file.gz"
```

### Security issues

- Password-based authentication is supported, with the caveat that
it is stored plaintext within the Juju controller.
- The previously-supported use of `ssh-private-key` is now DEPRECATED.

It's recommended that you implement the public key-based workflow documented above.

# Configuration and Usage

This layer adds the following configuration options:
- ssh-hostname
- ssh-username
- ssh-password

Once  [configure] those values at any time. Once they are set, the `sshproxy.configured` state flag will be toggled:

```
$ juju deploy mycharm ssh-hostname=10.10.10.10 ssh-username=ubuntu
$ juju run-action mycharm/0 get-ssh-public-key
Action queued with id: d2afaf3c-3c5a-4bc6-872b-fdb2ad4d6a45
$ juju show-action-output d2afaf3c-3c5a-4bc6-872b-fdb2ad4d6a45
results:
  pubkey: |
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJaWMK+/wb23mPQ+5Rb0gtljpE3DkAoJQ9oU3TWppDqJGX
    [...]
    MV1DQGijCcWQ== user@myhost
status: completed
timing:
  completed: 2017-08-03 15:39:21 +0000 UTC
  enqueued: 2017-08-03 15:39:16 +0000 UTC
  started: 2017-08-03 15:39:20 +0000 UTC
```


# Contact Information
Homepage: https://github.com/AdamIsrael/layer-sshproxy

[Juju]: https://jujucharms.com/about
[configure]: https://jujucharms.com/docs/2.0/charms-config
[scaling]: https://jujucharms.com/docs/2.0/charms-scaling
[relations]: https://jujucharms.com/docs/2.0/charms-relations
[leadership]: https://jujucharms.com/docs/2.0/developer-leadership
[created your charm]: https://jujucharms.com/docs/2.0/developer-getting-started
[action]: https://docs.jujucharms.com/2.5/en/actions
