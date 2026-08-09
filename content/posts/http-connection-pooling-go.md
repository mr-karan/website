+++
title = "Understanding HTTP Connection Pooling in Go"
date = 2025-12-23
draft = true
type = "post"
description = "Deep dive into Go's http.Transport internals - how connection pooling works, why it breaks, and how to fix it for production services."
in_search_index = true
[taxonomies]
tags = ["Go", "Networking", "Performance", "HTTP"]
[extra]
og_preview_img = "/images/http-connection-pooling.png"
+++

I've been writing Go services for a while now, and one thing that repeatedly bites people, even experienced engineers, is HTTP client configuration. The defaults work fine for CLI tools and one-off scripts. But the moment you're doing serious RPS to an upstream, things fall apart in ways that aren't obvious.

The classic symptom looks like this:

```bash
$ netstat -an | grep TIME_WAIT | wc -l
28437
```

Your service is choking because you ran out of ephemeral ports. Every request is creating a new connection, and old sockets are piling up in `TIME_WAIT`, waiting for the 60-second timeout to expire.

In this post, I want to dig into how Go's connection pooling actually works, not just the "use one client" advice, but the internals that explain *why* things break and how to fix them. This is the stuff I wish someone had told me five years ago.

## The cost of saying hello

When your Go program calls `http.Get("https://api.example.com/users")`, it doesn't just send your request. First, it has to establish a connection through several layers:

```text
┌─────────────┐                              ┌─────────────┐
│   Client    │                              │   Server    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  1. DNS: "What IP for api.example.com?"
       │────────────────────────────────────────────►
       │◄────────────────────────────────────────────
       │                                            │
       │  2. TCP: SYN ──────────────────────────────►
       │◄────────────────────────────────── SYN-ACK │
       │     ACK ───────────────────────────────────►
       │                                            │
       │  3. TLS: ClientHello ──────────────────────►
       │◄─────────────────────────── ServerHello... │
       │     ... (certificate, key exchange) ───────►
       │                                            │
       │  4. Finally: GET /users ───────────────────►
       │◄────────────────────────────── 200 OK {...}│
```

For services in the same AWS region with ~1ms latency, steps 1-3 add roughly 5-10ms before your request even starts. Do this for every request at 1000 req/s and you're burning CPU cycles on TLS handshakes instead of actual work.

Connection pooling keeps established connections around for reuse. You pay the handshake cost once, then reuse the pipe:

```text
First request:                    Second request:
DNS + TCP + TLS + HTTP            Just HTTP!
     (~10ms)                          (~1ms)
```

This is why reusing your `http.Client` matters so much. Creating a new client for each request means discarding the pool entirely.

## Inside the Transport: persistConn and the idle pool

Go's pooling lives in `http.Transport`. But unlike some languages where a "pool" is just a thread-safe list of sockets, Go treats connections as active entities, each one spinning up goroutines to handle reading and writing.

When the Transport establishes a connection, it wraps it in a `persistConn` struct. This struct spawns two goroutines:

- **`writeLoop`**: Receives requests via channel and writes them to the wire
- **`readLoop`**: Parses responses and decides if the connection can be reused

```text
┌─────────────────────────────────────────────────────────────────┐
│                         persistConn                              │
├─────────────────────────────────────────────────────────────────┤
│   ┌─────────────┐             ┌─────────────┐                   │
│   │  writeLoop  │             │  readLoop   │                   │
│   │  goroutine  │             │  goroutine  │                   │
│   └──────┬──────┘             └──────┬──────┘                   │
│          │                           │                           │
│          ▼                           ▼                           │
│      ┌─────────────────────────────────────┐                     │
│      │           TCP Connection             │                     │
│      └─────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

When you call `client.Do(req)`, your request goes to the `writeLoop` via a channel. The `writeLoop` writes headers and body to the wire. Your goroutine waits on a response channel. The `readLoop` parses the response and sends it back to you.

The critical step is what happens after: when the response body is fully consumed, the `readLoop` calls `putIdleConn`, adding the connection to a map:

```go
// Simplified view of Transport internals
type Transport struct {
    idleConn map[connectMethodKey][]*persistConn
    // "https|api.example.com:443" → [conn1, conn2]
}
```

This is why "leaking" a connection, by not closing the body, is so expensive. You're not just leaking a file descriptor, you're leaking two goroutines per connection. Do this at scale and your service runs out of OS threads.

## Body handling: what actually matters

Before we talk about body handling, a quick note on protocols: Go enables HTTP/2 by default for HTTPS connections. Most public APIs you hit are probably HTTP/2. So when does HTTP/1.1 body handling matter?

- Plain HTTP (non-TLS) connections
- Internal services that don't support HTTP/2
- Servers behind certain proxies
- Legacy APIs

For **HTTP/2**, connection reuse works differently, streams are multiplexed, so not reading one response doesn't corrupt others. But you should still close bodies promptly to release flow control resources.

For **HTTP/1.1**, body handling is critical. A connection is a sequential byte stream:

```text
[Request 1] → [Response 1 body...] → [Request 2] → [Response 2 body...]
```

If you close without reading, unread bytes remain in Go's buffer. The connection can't be reused, Go closes it instead of pooling it.

```go
resp, _ := client.Get("http://internal-api/data")  // HTTP/1.1
if resp.StatusCode == 200 {
    fmt.Println("Success!")
}
resp.Body.Close() // closed without reading = connection wasted
```

The fix, drain before close:

```go
resp, _ := client.Get("http://internal-api/data")
defer resp.Body.Close()

if resp.StatusCode == 200 {
    fmt.Println("Success!")
}

io.Copy(io.Discard, resp.Body) // drain for reuse
```

This pattern is common in production Go. Here's GitHub CLI doing exactly this:

```go
// From cli/cli - pkg/cmd/release/shared/fetch.go
if resp.StatusCode == http.StatusNotFound {
    _, _ = io.Copy(io.Discard, resp.Body)
    return "", ErrReleaseNotFound
}
```

## Does this actually matter?

I ran into this antipattern while building a load testing tool hitting an HTTP/1.1 server. The difference was dramatic:

**Without draining:**
```text
83,890 requests in 5 seconds
```

**With `io.Copy(io.Discard, resp.Body)`:**
```text
252,937 requests in 5 seconds
```

That's **3x throughput** from one line of code.

Why so dramatic? Without draining, every request created a new TCP+TLS connection. With draining, a handful of connections handled everything. The math is simple: if each handshake takes 5ms and you do 250,000 requests, that's 20 minutes of CPU time wasted on TLS alone.

For **HTTP/2**, the difference is less dramatic since streams are independent. But closing bodies promptly still matters for flow control and memory usage.

## Large responses: drain with a cap

If the response is 100MB and you don't need it, draining wastes bandwidth:

```go
// Drain up to 64KB, accept connection loss beyond that
io.CopyN(io.Discard, resp.Body, 64<<10)
resp.Body.Close()
```

Go's stdlib uses this pattern internally during redirect handling. You rarely need to read the entire body just to release a connection.

**Practical advice:** Always close bodies. Drain when you're hitting HTTP/1.1 servers and care about connection reuse. For HTTP/2, just closing promptly is usually enough.

## The MaxIdleConnsPerHost trap

Go's defaults:

```go
MaxIdleConns:        100  // total idle connections
MaxIdleConnsPerHost: 2    // idle connections per host
```

That `2` is almost always wrong for production.

If you're sending 50 concurrent requests to one upstream, Go creates 50 connections. When they complete, it keeps **2** in the pool and closes 48.

Next burst of 50 requests? Create 48 new connections again.

You're barely pooling. Each burst causes connection churn, TLS handshakes, and TIME_WAIT growth:

```bash
# During load, you'll see this growing
$ netstat -an | grep TIME_WAIT | wc -l
```

The fix:

```go
transport := &http.Transport{
    MaxIdleConnsPerHost: 50, // match your concurrency
}
```

## DNS pinning via keep-alive

Go's Transport doesn't cache DNS. But TCP connections effectively do, you resolved the IP when you dialed, and that connection sticks around until you close it or it times out.

If your upstream uses DNS-based load balancing (Route53 weighted records, Kubernetes services, Cloudflare), long-lived connections pin you to one backend IP. If that backend dies or DNS changes, you won't notice until the connection breaks:

```text
DNS record changes:  api.example.com → 10.0.1.50  (was 10.0.1.42)
Your connection:     Still talking to 10.0.1.42 (stale!)
```

The fix: set `IdleConnTimeout` lower than your DNS TTL to force periodic reconnection:

```go
transport := &http.Transport{
    IdleConnTimeout: 30 * time.Second, // force reconnect
}
```

This is a trade-off: you lose some connection reuse efficiency, but you gain resilience to DNS changes.

## The defer-in-loop trap

Quick note on a common mistake that trips people up:

```go
// BAD: bodies don't close until function returns
for _, url := range urls {
    resp, _ := client.Get(url)
    defer resp.Body.Close() // deferred to END of function!
}
```

Processing 10,000 URLs? You'll hold 10,000 open connections until the loop finishes. The connections time out on the server side, and you're back to the TIME_WAIT problem.

Fix with an anonymous function to scope the defer:

```go
for _, url := range urls {
    func() {
        resp, _ := client.Get(url)
        defer resp.Body.Close()
        io.Copy(io.Discard, resp.Body)
    }()
}
```

Or use a `break` pattern if you're feeling fancy.

## Failure signature table

When things go wrong, here's what to look for:

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| `cannot assign requested address` | TIME_WAIT exhaustion | Increase MaxIdleConnsPerHost, drain bodies |
| High p99 latency to one host | Pool too small, constant reconnects | Tune MaxIdleConnsPerHost ≥ concurrency |
| Requests to stale backend IP | Keep-alive pinning old DNS | Reduce IdleConnTimeout |
| Memory/goroutine growth | Not closing response bodies | Always close + drain |
| `connection reset by peer` | Server/LB killed idle conn | Set IdleConnTimeout < LB timeout |
| `use of closed connection` | Idle conn reaped mid-flight | Shorten IdleConnTimeout |

## Debugging with httptrace

When you're not sure if pooling is working, `httptrace` is your friend:

```go
trace := &httptrace.ClientTrace{
    DNSStart: func(info httptrace.DNSStartInfo) {
        log.Printf("DNS lookup: %s", info.Host)
    },
    ConnectStart: func(network, addr string) {
        log.Printf("Dialing: %s", addr)
    },
    GotConn: func(info httptrace.GotConnInfo) {
        log.Printf("reused=%v wasIdle=%v idleTime=%v",
            info.Reused, info.WasIdle, info.IdleTime)
    },
}

req, _ := http.NewRequest("GET", url, nil)
req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))
client.Do(req)
```

If `Reused` is always `false`, something's wrong, usually body handling or pool size. This is the fastest way to verify your pooling is actually working.

## Production-ready configuration

Here's what I typically use as a starting point for services doing serious traffic:

```go
func NewHTTPClient() *http.Client {
    transport := &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 20,  // tune to your concurrency
        MaxConnsPerHost:     100, // hard limit (Go 1.25.2+)
        IdleConnTimeout:     90 * time.Second,

        DialContext: (&net.Dialer{
            Timeout:   30 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,

        TLSHandshakeTimeout:   10 * time.Second,
        ResponseHeaderTimeout: 30 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
    }

    return &http.Client{
        Transport: transport,
        Timeout:   60 * time.Second,
    }
}

// Create once, reuse everywhere
var httpClient = NewHTTPClient()
```

And the request pattern I follow:

```go
resp, err := client.Do(req)
if err != nil {
    return err
}
defer resp.Body.Close()

// If you need the body:
body, err := io.ReadAll(resp.Body)

// If you don't need the body:
io.Copy(io.Discard, resp.Body)
```

For high-throughput services, we do millions of requests per minute for our alerting system at Zerodha, don't be afraid to set `MaxIdleConnsPerHost` to 100+. Memory is cheap, TLS handshake latency adds up.

## Summary

- **Connection pooling saves handshake overhead** by reusing connections
- **Always close response bodies** - leaking them leaks goroutines
- **Drain bodies for HTTP/1.1 reuse** (plain HTTP, internal services, legacy APIs)
- **`MaxIdleConnsPerHost=2` is too low** for almost any production service
- **DNS can get "pinned"** via long-lived connections; tune IdleConnTimeout accordingly
- **Use httptrace** to verify pooling is working

The difference between "works in dev" and "falls over in prod" is often just these settings.

Fin!
