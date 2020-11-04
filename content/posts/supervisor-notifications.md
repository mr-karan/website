+++
title = "Receiving notifications from Supervisor"
date = 2018-06-03T10:57:55+05:30
type = "post"
description = "Listening to Events in Supervisor"
in_search_index = true
[taxonomies]
tags = ["Python","Supervisor"]
+++

![Supervisor Events Zine](images/supervisor-zine.jpg "Supervisor Events Zine")

### Supervisor Events

I had a seemingly simple task which was to receive notifications any time a process managed by Supervisor restarts. I wanted a generic solution where I could get notifications for any change in the process state. `Supervisor Events` saved my day, although I would admit it wasn't straightforward to set up.

Supervisor uses `STDIN/STDOUT` mechanism to communicate with the event listener. You need to configure your event listener in such a way that it can understand the `STDIN` sent by Supervisor and also communicate back using `STDOUT`. You can write this event handler in any language you like as long as you conform to the specially formatted messages that Supervisor sends and expects. I had struggled the most at this step and my `google-fu` didn't help much in this case.

Supervisor by default will send these events even if no listener is configured. Once you have your own listener setup, you can execute any task you want, eg: send email/telegram/slack messages etc.

In order to configure your event listener, you need to add it to your `supervisor.conf`. Here's an example configuration:

```bash
[eventlistener:wowevent]
command=/home/work/testevent/test.py
events=PROCESS_STATE_STARTING
process_name=%(program_name)s_%(process_num)s
numprocs=1
autorestart=true
stderr_logfile=/home/work/testevent/logs/event_err.log
stdout_logfile=/home/work/testevent/logs/event.log
```

For the program to know that it has to send a notification at `wowevent` pool, you need to add the `events` key to the `program` section of `supervisor.conf`.

```bash
[program:myprog]
...
events=PROCESS_STATE_STARTING
...
```

Now everytime `myprog` is about to start, it will send an event to `wowevent` event pool. Your event listener which is configured at `/home/work/testevent/test.py` will handle the notification and execute tasks which you want to perform.

There are a bunch of event states that Supervisor captures, I was interested in knowing when my process has started, so I used `PROCESS_STATE_RUNNING`. You can take a look at all different event types [here](http://supervisord.org/events.html#event-types).

During all this experimentation I came across a bug (which I later found it is a [known issue](https://github.com/Supervisor/supervisor/issues/339), and an open bug since 4 years now). If you've been using Supervisor I am sure at least once you've been bitten by not `rereading` the config file and wondering why Supervisor isn't picking up changes in config file when you restart the Supervisor. So `reread` and `update` becomes a muscle memory after this event <i class="em em-stuck_out_tongue_closed_eyes"></i>.
The bug with events is that if you make any changes to the event group, `reread` doesn't pick up this change. I initially thought this must be the standard way Supervisor is behaving because I didn't change any `program` group. I randomly decided to change the event listener name and BAM! Supervisor read the new configuration and everything suddenly works! ARGH. Why do complex problems have such simple solutions <i class="em em-smiley"></i> (not a solution, rather a workaround, but you get the drift right?)

### Supervisor Event Listener Protocol

Supervisor sends a header which is a key value pair of meta-attributes about the process and event. This header looks something like

```bash
ver:3.0 server:supervisor serial:208 pool:mylistener poolserial:0 eventname:PROCESS_STATE_RUNNING len:69
```

The event listener `mylistener` will be in `ACKNOWLEDGED` state when Supervisor sends the event `PROCESS_STATE_RUNNING`. Now that the `myslistener` state has received this `ACKNOWLEDGED` state, the event listener will send `READY` back to Supervisor. This is to let Supervisor know that the listener has received the notification.
Supervisor puts the listener to `BUSY` state now and here you can do write your custom task. Supervisor waits for the task to get executed and when it does, the listener needs to communicate back with the result. This process is one full request-response cycle.

Let us write a simple Python script which will listen to Supervisor event notification and communicate back, all in a protocol Supervisor understands.

```python
import sys
import requests

import logging
logger = logging.getLogger('event_listener')
handler = logging.FileHandler('/home/user/prod/events/logs/response.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

Here I am just setting up basic logging structure since I want to keep the `stdout` messages separate from what Supervisor uses.

```python
def write_stdout(s):
    # only eventlistener protocol messages may be sent to stdout
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()
```

We have written helper functions which will be used to communicate with Supervisor. Now comes the `main` part (Sorry for bad pun! <i class="em em-blush"></i>)

```python
def main():
    while 1:
        # Hey Supervisor, I'm ready for some action
        write_stdout('READY\n')

        # Reading the header from STDIN
        line = sys.stdin.readline()
        write_stderr(line)

        # read event payload and print it to stderr
        headers = dict([ x.split(':') for x in line.split() ])
        data = sys.stdin.read(int(headers['len']))
        write_stderr(data)

        # add your events here
        notify_user()

        # transition from READY to ACKNOWLEDGED
        write_stdout('RESULT 2\nOK')
        logger.debug("It's all fine and dandy")

if __name__ == '__main__':
    main()
```

Let us break this into pieces.

```bash
write_stdout('READY\n')
```

We flush `READY` with a linefeed character (`\n`) to `STDOUT`. Supervisor has put mylistener to `BUSY` state now.

```bash
line = sys.stdin.readline()
write_stderr(line)
```

`line` would be the header which we discussed previously.

```bash
data = sys.stdin.read(int(headers['len']))
```

This part is interesting. Here, we capture the `len` key from the header and read the next `STDIN` line up to this many chars. The `data` would consist of our event payload.
Event payload looks something like:

```bash
processname:prog-restartv3_0 groupname:prog-restartv3 from_state:STOPPED tries:0ver:3.0 server:supervisor serial:25 pool:prog-restartv3 poolserial:3 eventname:PROCESS_STATE_STARTING len:76`
```

```python
notify_user()
```

This is the handler where you can send an email, send a request to API, log it to file etc.

```python
write_stdout('RESULT 2\nOK')
```

Finally, we tell Supervisor to put the listener from `BUSY` to `ACKNOWLEDGED` state, by sending a result structure. The result could be `FAIL` or `OK`, so you need to send `RESULT` followed by the length of the state variable. For example for `OK` you will send `RESULT 2\nOK` but for `FAIL` you have to send `RESULT 4\nFAIL`.

That's pretty much all you need to start receiving notifications from Supervisor every time your program changes its state. If you found this article useful, I'd love if you share this on [Twitter](https://twitter.com/intent/tweet?url=https%3A%2F%2Fmr-karan.github.io%2Fposts%2Fsupervisor-notifications&text=Receiving%20notifications%20from%20Supervisor) or [Facebook](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fmr-karan.github.io%2Fposts%2Fsupervisor-notifications) and let your friends know about it too.
