+++
title = "Docker"
date = 2021-09-21
type = "post"
in_search_index = true
[taxonomies]
til = ["CLI"]
+++

## Remove images locally with a wildcard:

```
docker rmi --force $(docker images | grep <image-name> | tr -s ' ' | cut -d ' ' -f 3) `
```

## Dockerhub Rate Limits

```
TOKEN=$(curl "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull" | jq --raw-output .token) && curl --head --header "Authorization: Bearer $TOKEN" "https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest" 2>&1 | grep ratelimit
```

## Docker Disk Usage

```
docker system df
```

## Use a custom DNS server in Docker

Docker makes it impossible to supply a `--dns` flag with `docker build` which makes it harder to use an internal service in your org. There are workarounds like `--add-host=xyz.internal:<IP>` but imagine doing this for dozen of services. Yep it's not maintainable, especially if the DNS records of these services change (for eg if they are behind ALB).

A cleaner solution is to forward the queries to your host DNS server itself. You can use various techniques like Split Tunnel (if your VPN supports that) or custom routing to different upstream DNS servers (eg with CoreDNS).

To make this happen, you need to edit the `/etc/docker/daemon.json` file:

```
{
        "dns": ["x.x.x.x"]
}
```

Docker uses `8.8.8.8` as a default, but if you override the above setting, it will start using the DNS server you provided.
