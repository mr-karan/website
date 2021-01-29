+++
title = "Setup Gitlab Runner with AWS ECR"
date = 2021-01-29T08:10:55+05:30
type = "post"
description = "How to setup Gitlab Runner with cross account AWS ECR access"
in_search_index = true
[taxonomies]
tags = ["Devops", "CI/CD"]
+++

There are some things you expect to just work. Sadly trying to make [Gitlab Runner](https://docs.gitlab.com/runner/) with [AWS ECR](https://aws.amazon.com/ecr/) turned out to be quite a daunting task and the little documentation in this area doesn't help. There's even a 4 years old [issue](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/1583) and everyone there is echoing the sentiment that this is unnecessarily a lot harder than it should have been.

Anyway, since I spent a lot of time figuring out how to make a Private Registry work with a cross-account ECR, I'm documenting these steps hoping it'll help someone someday :).

### The Problem

There are mainly 2 seemingly same but different problems when it comes to using ECR. Let's discuss both of them separately:

- Pulling a private image from ECR using the Docker Executor. For eg, if your `gitlab-ci.yml` looks like:

```yml
test-pull:
  image: $PRIVATE_ECR_IMAGE
  script:
    - echo "Hello World!"
```

In this case, the Docker Executor needs to be "authenticated" to AWS ECR so that it can pull `$PRIVATE_ECR_IMAGE`.

- Pulling a private image _inside_ the job. For eg, if you're using Kaniko:

``` yaml
docker-build:
  image: gcr.io/kaniko-project/executor:debug
  script:
    - |
      /kaniko ...
      # Inside this step, we use a PRIVATE_ECR_IMAGE defined in our `Dockerfile`.
```

In this case, [Kaniko](https://github.com/GoogleContainerTools/kaniko/) needs to be "authenticated" to AWS ECR so that it can pull `$PRIVATE_ECR_IMAGE`.

**NOTE** I prefer Kaniko over [DIND](https://docs.gitlab.com/ee/ci/docker/using_docker_build.html) as it is faster, doesn't require running the privileged container, caching is simplified, and is in general a lot simpler to setup.

### The Solution

So, for the first case, where you want to authenticate the Docker Executor to AWS ECR, you'll need 2 things:

1. Setup `DOCKER_AUTH_CONFIG` environment variable to  `{ "credsStore": "ecr-login" }` in the `config.toml` of the runner. For eg:

```
[[runners]]
  name = "Test"
  url = "https://gitlab.internal/"
  token = "REDACTED"
  executor = "docker"
  environment = ["DOCKER_AUTH_CONFIG={ \"credsStore\": \"ecr-login\" }"]
```

2. Now, we've specified the Credential Store for Docker, but we don't have this binary `docker-credential-ecr-login` in our runner. AWS provides [amazon-ecr-credential-helper](https://github.com/awslabs/amazon-ecr-credential-helper) which is a neat way of automatically authenticating with AWS ECR based on your Access Keys/IAM role. What does automatic mean here? So, the normal `docker login` is a basic auth command, where if you've to log in to ECR, you need to do something like:

```sh
aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com
```

This is problematic because the authorization token is valid for 12 hours. Further, you've to log in to multiple registry IDs separately. Managing this is a nightmare, so Docker instead of just relying on Basic Auth, came up with a neat mechanism: [docker-credential-helpers](https://github.com/docker/docker-credential-helpers). This allows you to keep your secret tokens in your Keystore. A new credential helper can be written in `Go` which implements the `credentials.Helper` interface. This is what [amazon-ecr-credential-helper](https://github.com/awslabs/amazon-ecr-credential-helper) does by offering various ways like AWS IAM Roles, Assumed Roles, Access Keys, etc to authenticate with ECR.

This is where I stumbled the most. I downloaded the binary from the [Github Releases](https://github.com/awslabs/amazon-ecr-credential-helper/releases/tag/v0.4.0) but this binary is statically compiled with `muslc` libraries.

However `gitlab/gitlab-runner` is based on the `ubuntu` docker image, so the above binary never worked. The strangest thing was the unhelpful error message that `sh` returned as explained in this [post](https://forum.gitlab.com/t/bin-sh-eval-line-97-mybinary-not-found/27125/3).

To make things easier, I baked my own `gitlab-runner` image with the above binary compiled inside the image
using `go get`:

```Dockerfile
FROM ubuntu:20.04 AS build
ENV DEBIAN_FRONTEND=noninteractive 
RUN : \
 && apt-get update \
 && apt-get install --no-install-recommends -y git golang-go ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
;
RUN go get -u github.com/awslabs/amazon-ecr-credential-helper/ecr-login/cli/docker-credential-ecr-login
WORKDIR /build
RUN mv /root/go/bin/docker-credential-ecr-login .

FROM gitlab/gitlab-runner:v13.8.0 AS deploy
COPY --from=build /build/docker-credential-ecr-login /usr/local/bin/docker-credential-ecr-login
```

The above image bakes in the `docker-credential-ecr-login` binary and also puts it under `/usr/local/bin` so it'll be available under `$PATH` to the Docker engine.

With the above 2 things, if the runner's server (EC2 instance/K8s pod) has access to the ECR image, it should be able to pull.

Now coming to the 2nd problem, where we wanted `kaniko` to authenticate to ECR, things are a bit simpler:

- Kaniko comes with `docker-credential-ecr-login` baked in. All you need to do is add the following to `~/.docker/config.json` as explained [here](https://github.com/GoogleContainerTools/kaniko/blob/master/README.md#pushing-to-amazon-ecr).

```
{ "credsStore": "ecr-login" }
```

Next, we need to mount the AWS Credentials to Kaniko's image so that it can use AWS SDK to perform a login to ECR. We do that by using `volumes` of the `runner`:

```
[runners.docker]
volumes = ["/home/ubuntu/runners/test/aws-credentials:/root/.aws/credentials:ro"]
```

This mounts the `aws-credentials` file from the host inside the container which the runner spawned (`kaniko` in this case).

A sample `aws-credentials` file if you're using a cross-account access can look like:

```
[default]
role_arn=arn:aws:iam::ACCOUNT_ID:role/assume-role-{{ROLE_NAME}}
credential_source=Ec2InstanceMetadata
region=ap-south-1
```

You can put in your normal AWS Keys or leave them blank if you want to use your IAM Role. With mounting the AWS Credentials inside Kaniko's container, you can authenticate to cross-account ECRs as well (once you set up the whole assumed-role/trusted entities flow).

### Sample Runner

If you want to take a look at how the complete flow looks like:

- Start the Runner service using `docker-compose`:

```yml
version: '3.7'

services:

  test:
    # As explained above, this image has `docker-credentials-ecr-login` baked in.
    image: {{ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/custom/gitlab-runner:13.8.0
    restart: always
    volumes:
      # Automatically created; config.toml.
      - './test/runner-config:/etc/gitlab-runner'
      # Mount AWS Credentials for Docker Executor to authenticate.
      - './test/aws-credentials:/root/.aws/credentials:ro'
      # Mount Docker Socket so that executor can communicate with it.
      - '/var/run/docker.sock:/var/run/docker.sock'
```

- Register a new runner:

```
docker-compose exec test register
```

Fill in the basic info and edit `./test/runner-config.toml` with the following options:

```
[[runners]]
  name = "Test"
  executor = "docker"
  environment = ["DOCKER_AUTH_CONFIG={ \"credsStore\": \"ecr-login\" }"]
  [runners.docker]
    volumes = ["/home/ubuntu/runners/test/aws-credentials:/root/.aws/credentials:ro"]
```

## Conclusion

Honestly, this was a lot of trial and error to figure out how to use private images with Gitlab. Some important links and references that helped me figure this out:

- [https://gitlab.com/bmares/gitlab-runner-ecr-auth-example/](https://gitlab.com/bmares/gitlab-runner-ecr-auth-example/)
- [https://gitlab.com/gitlab-org/gitlab-runner/-/issues/1583#note_84649153](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/1583#note_84649153)

Fin!
