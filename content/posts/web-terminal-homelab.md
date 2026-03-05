+++
title = "A Web Terminal for My Homelab"
date = 2026-03-05
type = "post"
description = "Setting up ttyd + tmux for browser-based shell access to my homelab server"
in_search_index = true
[taxonomies]
tags= ["Homelab", "Devops"]
[extra]
og_preview_img = "/images/web-terminal-homelab.png"
+++

I often need quick shell access to my homelab server from my phone or tablet. SSH apps on mobile are clunky, and sometimes I just want to check on something without pulling out a laptop. The solution: a web-based terminal at `terminal.mrkaran.dev`.

## The Stack

[ttyd](https://github.com/tsl0922/ttyd) is a simple tool that shares a terminal over the web. It wraps any command into a browser-accessible terminal using WebSockets and xterm.js. Pair it with tmux, and you get persistent sessions that survive browser disconnects.

The key trick is using `nsenter` to break out of the container and into the host's namespaces. This gives you a real host shell, not a container shell, while still being deployable as a Docker stack.

## Docker Compose

```yaml
services:
  ttyd:
    image: tsl0922/ttyd
    container_name: ttyd
    restart: unless-stopped
    command: >
      ttyd
        -W
        -p 7681
        -t fontSize=15
        -t 'theme={"background":"#1a1b26","foreground":"#c0caf5"}'
        nsenter
        -t 1
        -m -u -i -p
        --
        /bin/bash -l -c
        "tmux new-session -A -s main"
    privileged: true
    pid: "host"
    networks:
      - public_proxy
```

Breaking this down:

- `-W` enables writable mode (ttyd is read-only by default).
- `nsenter -t 1 -m -u -i -p` enters the host's mount, UTS, IPC, and PID namespaces via PID 1. The net namespace is intentionally skipped so the container stays on the Docker network, reachable by the reverse proxy.
- `tmux new-session -A -s main` creates or reattaches to a persistent tmux session called "main". Close the browser tab, open it again later, and you're right back where you left off.
- `pid: "host"` is required for `nsenter` to see the host's PID 1.
- `privileged: true` grants the permissions needed for namespace manipulation.

## Caddy Reverse Proxy

The terminal sits behind Caddy with TLS via Cloudflare DNS challenge, same as every other service:

```
terminal.mrkaran.dev {
    reverse_proxy ttyd:7681

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }

    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websockets ttyd:7681
}
```

WebSocket support is essential here since xterm.js communicates entirely over WebSockets.

## Security

This is behind Tailscale, so only devices on my tailnet can reach it. No additional authentication layer needed. If you're exposing this to the public internet, you'd want at minimum basic auth (`ttyd -c user:pass`) or a forward auth proxy.

## The Result

![Web terminal in the browser](/images/web-terminal-homelab.png)

A full terminal in the browser with persistent tmux sessions. Works great on mobile for quick checks, and on a tablet it's practically indistinguishable from a native terminal. The total setup is about 25 lines of YAML and took under 5 minutes to deploy.
