+++
title = "GitOps approach to Continuous Delivery for Kubernetes"
date = 2019-11-11T10:57:55+05:30
type = "draft"
description = "Setup a deployment pipeline using Gitlab CI/CD for continuous delivery to AWS EKS"
in_search_index = true
[taxonomies]
tags = ["Kubernetes","CI/CD", "Devops"]
+++

In this post, I'd like to share my experience and learnings about configuring a deployment pipeline for Kubernetes. I'll be using Gitlab CI/CD and AWS EKS to demonstrate the concept, but the core idea remains the same: _all changes must come declaratively from a single source of truth_. `GitOps` is a relatively newer term in the town but goes back to the fundamentals of _Infra as Code_.

GitOps fundamentally is an operating model to perform tasks on Kubernetes related to deployments, configuration, secrets and monitoring workloads. All kind of changes must be performed via a single place, which happens to be a `git` repo. Benefits of that are what basically benefits of version controlling the code is. So why treat infra as any different? `git` happens to be the single source of truth for your infra, rollbacks are easy as reverting to last known good configuration and every change can be observed/verified.

## Goals

A lot of tutorials/blog posts hitherto cover a very basic scenario where they do `kubectl apply` and voila the deployment's live. However we all know things are very different (to say the least) in production, so this post will cover all aspects of deployment:

- Creating Manifests
- Environment Promotion
- Handling config and secrets
- Authorization of CI/CD in the cluster

### Basics

A GitOps workflow looks like:

### Push vs Pull

There are 2 approaches to how you can handle deployments to a cluster. In a Pull based approach, the cluster runs a synch controller program which continmioously syncs the state of cluster with a Git repo. Any changes you make to the Git repo will be synced automatically in cluster. The idea is that there should be no drift in the desired state via Git repo and the actual state of cluster. Flux, Argo are good tools if you want a Pull based pipeline. The merits of Pull based pipeline is it's more secure, since the deployment is actually happening inside cluster and no external sytstem needs to communicate to your production infra. The demerits are sometimes you've to wait for the changes to be synced (every controller runs these sync process in a loop with a sleep which can be configured). Also using any kind of preprocessing tools like Kustomize becomes difficult, since Flux just syncs the state and applies those changes. Handling of secrets is yet another concern, you need to look . And finally GitOps is a relatively newer tech in market so GitOps tooling is still nascent and like with any other relatively (non battle tested) software you're gonna find bugs.

Push Approach however is a traditional CD approach, where the CD server talks to the cluster and applies changes through commands. In context of normal EC2 deployments, those commands could be SSH into server, running ansible playbook etc. In context of K8s however `kubectl` does the magic for us. The CD server needs to talk to the K8s API server and run kubectl commands to change the cluster state.
The merits of this approach are you can run all sorts of commands inside deployment pipeline and make it fully customisable. Handling of secrets also can be handled natively (like Gitlab env variables) or encrypted in `git`.
The demerits is that your production cluster is now exposed to your CD server.

Overall, if you have an airgapped CD server with no inbound ports open, access controll the user auth to CD, I found the Push approach to be more preferable. YMMV.

## Writing the pipeline

I've created a docker [image](https://github.com/mr-karan/eks-gitops) `eks-gitops` which I'll be using throughout the pipeline. This container image contains popular tools like `kustomize`, `kubeval` etc and scripts to configure access to cluster using `kubectl` using `aws-iam-authenticator`. I've written more about how RBAC works inside EKS [here](https://mrkaran.dev/posts/intro-rbac-kubernetes/).

_Excerpt from `.gitla-ci.yml`_:

```yml
# Use this as base image for all jobs unless overriden
default:
  image:
    name: mrkaran/eks-gitops:latest
    entrypoint: ["/bin/sh", "-c"]
### Pipeline
stages:
  - validate
  - deploy
```

### Prepare the manifests

I use `Kustomize` to prepare the manifests. Advantage of `Kustomize` is writing template free YAMLs but still be able to customise them heavily using overlays. For different environments, you can apply certain changes like increasing resource requests, adding more storage, while keeping the base same.

Here's a folder structure (from a real GitOps repo) I follow for manifests:

```shell
.
├── base
│   ├── deployments
│   │   ├── app.yml
│   │   ├── celery.yml
│   │   └── nginx.yml
│   ├── ingresses
│   │   └── web.yml
│   ├── kustomization.yaml
│   ├── services
│   │   ├── app.yml
│   │   ├── nginx.yml
│   │   └── redis-headless.yml
│   ├── statefulsets
│   │   └── redis.yml
│   └── volumes
│       └── redis.yml
├── kubekutter.yml
├── Makefile
├── overlays
│   ├── dev
│   └── prod
│       ├── configs
│       │   ├── app-config.env
│       │   └── app-nginx.conf
│       ├── kustomization.env.yml
│       ├── namespace.yml
│       ├── patches
│       │   ├── configure-configmap-volume.yml
│       │   ├── modify-alb.yml
│       │   └── resource-limits.yml
│       └── rbac.yml
└── README.md
```

**Shameless Plug**: I created `kubekutr` which makes managing of these manifests using `kustomize` a breeze.

Some things to note here:

- Inside `base/`, I keep all the `base` resources required for the app to run. The resources can be `Service`, `Deployment`, `Ingress` etc.
- Inside `overlays` there are multiple folders for different environment. This is very crucial as we want to separate the production config with a UAT config. Last-mile configuration to the base becomes very easy with this folder structure, since you only now need to build the manifests by targetting a specific folder in CI.
- Inside `overlays/{env}/patches` are all the "patches" you want to do to the base resource. Think like replica count, ALB subnets (since different env can be in different VPCs), increasing resource limits and stuff like that.
- `rbac.yml` abd `namespace.yml` is the only missing piece because it's like a chicken and egg problem. I cannot deploy directly (at first go) from a CI/CD if I don't have a namespace created since the CD server is configured only has limited namespaced restricted access. So unless I create a namespace, add proper RBAC for the CD server I cannot do any deployments from CD. Note however this is only a first time step, which I guess is okay.

### Lint yo manifest

I'm using `kubeval` to lint the manifests. The manifests have to prepared by `kustomize`. `CI_ENVIRONMENT_NAME` is set by `Gitlab` when you specify an environment for a job. Don't sweat about this part, I'll describe it more as we proceed.

```yml
# Validate the yaml using kubeval
.lint:
  extends: .prepare-manifest
  stage: validate
  script:
    - echo "Linting manifest for ${CI_ENVIRONMENT_NAME}"
    - kustomize build overlays/$CI_ENVIRONMENT_NAME --load_restrictor none | kubeval
```

### Setup environment

You can define environment name as:

```yml
# Create an environment to record all jobs for this env
.prod: &prod
  environment:
    name: prod
    url: https://prod.site
.dev: &dev
  environment:
    name: dev
    url: https://dev.site
```

Any job which is to be executed in a particular environment can include this variable and `CI_ENVIRONMENT_NAME` will be automatically set.

A cool feature of Gitlab is that you can restrict Variables scoped to the environment they are defined in.

### Configure Secrets

All secrets are defined as Environment Variables in Gitlab CD pipeline. While running the job, the runner has access to these variables and with the help of `secretGenerator` in `kustomize`, the `Secret` is created.

I use `secretGenerator` because any time a K8s secret changes, kustomize appends with a new suffix, which makes the Replication Controller believe that they deployment has changed. So a new deployment is automatically triggered.

### Authenticate to cluster

EKS uses aws-iam-authenticator and uses IAM access roles to allow the cluster to perform actions. Since this is a push based pipeline, you need to allow the access from your CD server to port 443.

### Deploy changes

This is as simple as `kubectl apply` which configures all the changes and diff between cluster and real world state.

Here's a full gitops repo if you're interested in checking it out:
