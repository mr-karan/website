+++
title = "Docker CLI Snippets"
date = 2023-02-02
type = "til"
description = "CLI"
in_search_index = true
[taxonomies]
tags = ["Docker"]
+++

## Remove images locally with a wildcard:

```sh
docker rmi --force $(docker images | grep <image-name> | tr -s ' ' | cut -d ' ' -f 3) `
```

## Remove images using xargs

I wanted to remove all containers that had the word `outline` in their name. I used the following command:

```sh
docker ps | grep outline | awk '{print $1}' | xargs docker rm -f
```

## Dockerhub Rate Limits

```sh
TOKEN=$(curl "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull" | jq --raw-output .token) && curl --head --header "Authorization: Bearer $TOKEN" "https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest" 2>&1 | grep ratelimit
```

## Docker Disk Usage

```sh
docker system df --verbose
```

## Stop all containers


```sh
docker stop $(docker ps -a -q)
```
