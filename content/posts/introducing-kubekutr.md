+++
title = "Introducing kubekutr"
date = 2019-12-30T08:10:55+05:30
type = "post"
description = "kubekutr is a cookie cutter template tool for generating Kubernetes resource manifests"
in_search_index = true
[taxonomies]
tags = ["kubernetes", "golang"]
+++

![](https://raw.githubusercontent.com/mr-karan/kubekutr/master/logo.png)

[kubekutr](https://github.com/mr-karan/kubekutr/) was born out of my frustration of organising K8s resource manifests files/directories. For the uninitiated, K8s lets you hold the state of your cluster [declaratively](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/) as "manifest" files. K8s does so by a lot of asynchronous control loops to check whether the desired state matches the real world state and in case of drifts, it resets back to the user desired state (I oversimplified this, but hope you get the drift ;)). These files are predominantly `YAML` but there's support for `JSON` as well. Anyway, to create these manifest files for a production level project is quite a bit of manual labour. The API spec of every resource in Kubernetes is quite [daunting](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.14/) and overwhelming. There are tools like Helm which abstract away the complexity of these YAML with it's own templating system. There are quite a lot of these charts available for 3rd party apps [here](https://github.com/helm/charts). The idea is you populate the Chart with just your own config "values" and you've a deployment ready in no time. Admittedly this works quite well for something you want to take out for a quick spin but personally I am not quite a fan of hiding away the complexity with a _magic_ layer. Also, the problem with Helm was the "Chart" (and templates) still had to be written by someone if you have a [bespoke](https://github.com/kubernetes-sigs/kustomize/blob/master/docs/glossary.md#bespoke-configuration) application. Helm is more geared towards common off the shelf apps like DBs, Key Value stores, web proxies etc.

I found out [kustomize](github.com/kubernetes-sigs/kustomize) few months back and quite happy with it's approach towards managing manifests. The basic idea behind `kustomize` is that you create a _base_ and any kind of "customisations" must come as _overlays_. This is such a powerful technique over wrangling templates. `kustomize` A common approach is to name these _overlays_ based on the environment. For example, `dev` deployment can have `replicas: 1` for a pod, but `prod` can apply a "patch" to update with `repliacs: 3`. This way of separating two environments helps a lot when you follow [GitOps](https://www.weave.works/technologies/gitops/) approach of deployment. All fine and good, until I realised I spent way too much time on copy-pasting the bases for different projects and manually editing these files for the new project config.

Then I did what any other programmer would do, spend some more time to automate :P And that is how `kubekutr` was born. (Quite an anticlimax I know!)

`kubekutr` is a really simple tool to bootstrap a Kustomize `base`. `kubekutr` reads a config file, templates out different resources and produces them as YAML files. Now, I know a lot of you reading this would be going _Another damn templating solution_ in your mind and while that reaction is warranted, given that we have 200+ [tools](https://docs.google.com/spreadsheets/d/1FCgqz1Ci7_VCz_wdh8vBitZ3giBtac_H8SBw4uxnrsE/edit#gid=0) in the community (everyone trying to solve similar problems in their own ways), I _legit_ could not find a simple enough tool which would let the boring part of scaffolding a base out of my way and let me focus on what's more important: the actual deployment. Hence I just decided to roll out my own solution which is the best one according to [IKEA effect](https://en.wikipedia.org/wiki/IKEA_effect) (_just kidding_).

### Workflow

So, let's say you need to create a Nginx deployment, the `kubekutr` `config.yml` would look something like this:

```
deployments:
  - name: nginx
    replicas: 1
    labels:
      - name: 'service: nginx'
    containers:
      - name: nginx
        image: 'nginx:latest'
        portInt: 80
        portName: nginx-port
services:
  - name: nginx
    type: ClusterIP
    port: 80
    targetPort: 80
    labels:
      - name: 'service: nginx'
    selectors:
      - name: 'service: nginx'
```

To create the `base`:

`kubekutr -c config.yml scaffold -o nginx-deployment`

`nginx-deployment` folder is initialised and you can view `deployments/nginx.yml` and `service/nginx.yml` which `kubekutr` created.

```
$ tree nginx-deployment

|-- base
|   |-- deployments
|   |   `-- nginx.yml
|   |-- ingresses
|   |-- services
|   |   `-- nginx.yml
|   `-- statefulsets
```

```
$ cat base/deployments/nginx.yml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    service: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      service: nginx
  template:
    metadata:
      labels:
        service: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
          - containerPort: 80
            name: nginx-port
```

```
$ cat base/services/nginx.yml

apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    service: nginx
spec:
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
  type: ClusterIP
  selector:
    service: nginx
```

You can now use the generated folder as a Kustomize `base`.

### Non Goals

`kubekutr` isn't meant to replace the existing tools, it's just a real simple cookie cutter approach to `kustomize` bases and that's pretty much it. `kustomize` is native to Kubernetes and exposes the full API spec to end users. I feel that is much more better approach than templating solutions, the users must be exposed to the standard conventions rather than a random tool's own config fields. The benefits are the same conventions can then be used across a wide variety of tools (like `kubekutr`) and users are in better control of the underlying resources. Adding a layer of magic also makes it harder to debug when shit goes down. Hence `kubekutr` chose `kustomize` to do all the heavy lifting of managing manifests.

There's a lot of scope of improvements, but I wanted to just Ship It! and get some initial feedback. Let me know your thoughts on this :)

Fin!
