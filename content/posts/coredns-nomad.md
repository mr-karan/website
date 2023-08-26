+++
title = "Building a CoreDNS plugin"
date = 2023-01-05T00:00:00+05:30
type = "post"
description = "Short notes on writing a CoreDNS plugin for Nomad native service discovery"
in_search_index = true
[taxonomies]
tags = ["golang", "coredns"]
+++

CoreDNS is an extensible DNS server (which is actually a fork of Caddy v1) that can be used to serve DNS records for a domain. It is written in Go and is very easy to extend. It has a plugin system that allows you to write your own plugins to extend its functionality. In this post, I will be writing a plugin for CoreDNS that will allow it to serve DNS records for Nomad services.

I recently came across a [niche use case](https://github.com/hashicorp/nomad/issues/12588#issuecomment-1368679059) which required me to use a resolver address for querying Nomad services. Currently Nomad native service discovery is only possible via `consul-template` (which renders static block of address/port of services) and HTTP API. I felt adding a DNS interface would be a nice add-on.

Rather than writing and implementing all the boring crux of a DNS server, it's better to extend on an existing server. CoreDNS fits in well here, it's also used by K8s for service discovery. CoreDNS has an extensible plugin system which allows you to chain multiple different plugins for handling a request. Stuff like logs/metrics/caching comes for free with CoreDNS in form of a plugin.

CoreDNS docs have a [handy guide](https://github.com/coredns/coredns/blob/master/plugin.md#writing-plugins) on how to write a plugin from scratch, so I won't cover that again here. These are just my short notes on how I locally developed the plugin, tested and some problems I encountered during the process.

## Developing the plugin

Firstly, you need to clone CoreDNS repo. Then, using the [example](https://github.com/coredns/example) plugin provided, you can create a new repository for your own plugin.

To make CoreDNS aware about this plugin, you need to add it to the `plugin.cfg` file. This file is used by the build script to generate the plugin list. The order of plugins matter here as they define how the request is handled. For example, if you want to log all the requests, you need to add the `log` plugin before your plugin.

To add an external plugin this is the format used:

```sh
nomad:github.com/mr-karan/coredns-nomad
```

However, since we are developing the plugin locally, we need to add a `replace` directive in `go.mod` file to point to the local plugin directory.

```go
replace github.com/mr-karan/coredns-nomad => ../../coredns-nomad
```

Next, you can run `make` in `coredns` repository. It'll build the binary and place it in `coredns` directory. You can run this binary to test your plugin. To check if the plugin indeed exists in the binary, you can use the following command

```sh
./coredns -plugins | grep nomad
```

## Handling requests

The `ServeDNS` function is used to handle the DNS request by the plugin. It takes a `context.Context` and a `dns.ResponseWriter` as arguments. The `dns.ResponseWriter` is used to write the response back to the client. The `ServeDNS` function returns an `int` which is the status code of the response. The status code is used by the next plugin in the chain to determine if it should handle the request or not.

Since the `nomad` plugin expects a query in format of `service.namespace.nomad`, it validates the query and extracts the service name and namespace from it. If the query is invalid, it returns `dns.RcodeServerFailure` status code. If the query is valid, it queries the Nomad API for the service and returns the response.

```go
func (n Nomad) ServeDNS(ctx context.Context, w dns.ResponseWriter, r *dns.Msg) (int, error) {
	state := request.Request{W: w, Req: r}
	qname := state.Name()
	qtype := state.QType()

	// Split the query name with a `.` as the delimiter and extract namespace and service name.
	// If the query is not for a Nomad service, return.
	qnameSplit := dns.SplitDomainName(qname)
	if len(qnameSplit) < 3 || qnameSplit[2] != "nomad" {
		return plugin.NextOrFailure(n.Name(), n.Next, ctx, w, r)
	}
	namespace := qnameSplit[1]
	serviceName := qnameSplit[0]

...

```
The plugin handles A,AAAA and SRV record requests currently. Since A/AAAA records can only contain an IP address, SRV records can be used to advertise the port number.

```go
		// Check the query type to format the appriopriate response.
		switch qtype {
		case dns.TypeA:
			m.Answer = append(m.Answer, &dns.A{
				Hdr: header,
				A:   addr,
			})
		case dns.TypeAAAA:
			m.Answer = append(m.Answer, &dns.AAAA{
				Hdr:  header,
				AAAA: addr,
			})

...

```

### Caching

While some coredns plugins have an in-built support for caching the records to avoid a lookup to Nomad server everytime (which can get expensive), I decided to skip the caching implementation. This is because `coredns` itself has a `cache` plugins which supports a lot of various options for controlling the cache. In my testing, just using this `cache` plugin was sufficient to avoid Nomad lookups each time a query came in. 


## Testing the plugin

I created a fake HTTP test server and added the URI paths which the Nomad Go client uses to query the Nomad API. This way I could test the plugin without having to run a Nomad cluster locally.

```go
	// Setup a fake Nomad server.
	nomadServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		default:
			t.Errorf("Not implemented: %v", r.URL.Path)
			return
		case "/v1/service/example":
			w.Write([]byte(`[{"Address":"1.2.3.4","Namespace":"default","Port":23202,"ServiceName":"example"}]`))
		case "/v1/service/fakeipv6":
			w.Write([]byte(`[{"Address":"1:2:3::4","Namespace":"default","Port":8000,"ServiceName":"fakeipv6"}]`))
		case "/v1/service/multi":
			w.Write([]byte(`[{"Address":"1.2.3.4","Namespace":"default","Port":25395,"ServiceName":"multi"},{"Address":"1.2.3.5","Namespace":"default","Port":20888,"ServiceName":"multi"},{"Address":"1.2.3.6","Namespace":"default","Port":26292,"ServiceName":"multi"}]`))
		case "/v1/service/nonexistent":
			w.Write([]byte(`[]`))
		}
	}))
```

## Usage Example

Here are some examples of how this plugin works. The Corefile I've used is:

```txt
nomad:1053 {
    errors
    debug
    health
    log
    nomad {
		address http://127.0.0.1:4646
        ttl 10
    }
    prometheus :9153
    cache 30
}
```

On running `coredns`, it connects to a local Nomad agent which is running at `http://127.0.0.1:4646`. I'm running a `redis` job in Nomad, so I can query the service using the following command:

```sh
nomad service info -namespace=default redis                 
Job ID  Address              Tags  Node ID   Alloc ID
redis   192.168.29.76:25395  []    9e02c85b  95170495
redis   192.168.29.76:20888  []    9e02c85b  a1cf923c
redis   192.168.29.76:26292  []    9e02c85b  a9d1181a
```

Now, the same query can also be handled using the DNS server running by `coredns`:

```bash
doggo redis.default.nomad @tcp://127.0.0.1:1053
NAME                	TYPE	CLASS	TTL	ADDRESS      	NAMESERVER     
redis.default.nomad.	A   	IN   	10s	192.168.29.76	127.0.0.1:1053	
redis.default.nomad.	A   	IN   	10s	192.168.29.76	127.0.0.1:1053	
redis.default.nomad.	A   	IN   	10s	192.168.29.76	127.0.0.1:1053
```

Quering an SRV record is also possible:

```bash
dig +noall +answer +additional redis.default.nomad @127.0.0.1 -p 1053 SRV
redis.default.nomad.	10	IN	SRV	10 10 25395 redis.default.nomad.
redis.default.nomad.	10	IN	SRV	10 10 20888 redis.default.nomad.
redis.default.nomad.	10	IN	SRV	10 10 26292 redis.default.nomad.
redis.default.nomad.	10	IN	A	192.168.29.76
redis.default.nomad.	10	IN	A	192.168.29.76
redis.default.nomad.	10	IN	A	192.168.29.76
```

## Code

You can checkout the source code [here](https://github.com/mr-karan/coredns-nomad/).

Fin!
