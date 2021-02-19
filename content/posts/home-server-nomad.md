+++
title = "Running Nomad for home server"
date = 2021-02-14T08:10:55+05:30
type = "post"
description = "Setting up a single node Nomad and Consul server to deploy self hosted workloads."
in_search_index = true
[taxonomies]
tags = ["Nomad","DevOps", "Terraform", "Homeserver"]
[extra]
og_preview_img = "/images/nomad-hydra.png"
+++

It's been a long time since I've written a post on Hydra (my home server). I use Hydra as a testbed to learn new tools, workflows and it just gives me joy to self-host applications while learning something in return.

## History

A brief history of how [Hydra's](https://github.com/mr-karan/hydra) setup evolved over time:

[2019](https://mrkaran.dev/posts/home-server-setup/): 

- A pretty minimal K3s setup deployed on 2 RPi4 nodes. I couldn't continue with this setup because:
  - Some of the apps didn't have ARM-based image (this was 2019, pre M1 hype era).
  - Didn't want to risk deploying persistent workloads on RPi.
  - A lot of tooling to deploy workloads was missing (storing env variables for eg.).
  - It was so boring to write YAML (that I also did at work). Didn't give me joy.

[2020 First Half](https://mrkaran.dev/posts/home-server-updates/):
- RPi 2x Nodes + K3s + DO Droplet. Tailscale for networking.
  - This was a considerable step up from the previous setup. I deployed a DO node and added [Node Labels](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes/) to deploy persistent workloads on DO Node only.
  - I used my own tooling [Kubekutr](https://github.com/mr-karan/kubekutr/) + Kustomize which helped with version control of my configs.
  - Took quite a bit of time to onboard new services. Got lazy, didn't host much apart from initial 3-4 applications.
  - Writing long YAMLs. No joy.

2020 Second Half:
- Single node on DO. Terraform for deploying Docker containers.
  - I believe the third iteration nailed it for me. I kept the setup super simple, used Terraform for deploying workloads as Docker containers.
  - Used Terraform extensively for setting up the node, Cloudflare records, DO firewall rules.
  - Time to onboard new services reduced from a couple of hours to a few minutes. This was a huge win for me. I deployed around 10-15 new services to try it out on the server directly.
  - Writing HCL is actually a much better experience than YAML.

## Why Nomad

![image](/images/nomad-hydra.png)

Around a month back, [Kailash](https://nadh.in/) had asked about feedback on [Nomad](https://www.nomadproject.io/). We at [Zerodha](https://zerodha.com/) (India's largest stock broker) are evaluating it to migrate our services to Nomad from Kubernetes (more on this later). It was almost 2 years since I last saw Nomad so it was definitely worth re-evaluating (esp since it hit 1.0 recently). I wanted to try out Nomad to answer a personal curiosity: _What does it do differently than Kubernetes?_ No better way than actually getting hands dirty, right?!

After following the brief tutorials from the [official website](https://learn.hashicorp.com/nomad) I felt confident to try it for actual workloads. In my previous setup, I was hosting quite a few applications (Pihole, Gitea, Grafana etc) and thought it'll be a nice way to learn how Nomad works by deploying the same services in the Nomad cluster. And I came in with zero expectations, I already had a nice setup which was reliable and running for me. My experience with a local Nomad cluster was joyful, I was able to quickly go from 0->1 in less than 30 minutes. This BTW is a strong sign of how easy Nomad is to get started with as compared to K8s. The sheer amount of different concepts you've to register in your mind before you can even deploy a single container in a K8s cluster is bizarre. Nomad takes the easy way out here and simplified the concepts for developers into just three things:

```
job
  \_ group
        \_ task
```

- Job: Job is a collection of different groups. Job is where the constraints for type of scheduler, update strategies and ACL is placed. 
- Group: Group is a collection of different tasks. A group is always executed on the same Nomad client node. You'll want to use Groups for use-cases like a logging sidecar, reverse proxies etc.
- Task: Atomic unit of work. A task in Nomad can be running a container/binary/Java VM etc, defining the mount points, env variables, ports to be exposed etc.

If you're coming from K8s you can think of Task as a Pod and Group as a Replicaset. There's no equivalent to Job in K8s. BUT! The coolest part? You don't have to familiarise yourself with all different types of Replicasets (Deployments, Daemonsets, Statefulsets) and different ways of configuring them.

Want to make a normal job as a periodic job in Nomad? Simply add the following block to your existing Job:

```hcl
periodic {
  cron = "@daily"
}
```

You want to make a service run as a batch job (on all Nomad nodes -- the equivalent of Daemonset in K8s)? Simply make the following change to your existing job:

```diff
-type="service"
+type="batch"
```

You see **this** is what I mean by the focus on UX. There are many many such examples which will leave a nice smile on your face if you're coming from K8s background.

I'd recommend reading [Internal Architecture](https://www.nomadproject.io/docs/internals/architecture) of Nomad if you want to understand this in-depth.

## Architecture

Tech stack for Hydra:

- Tailscale VPN: Serves as a mesh layer between my laptop/mobile and DO server. Useful for exposing internal services.
- Caddy for reverse proxying and automatic SSL setup for all services. I run 2 instances of Caddy:
	- Internal: Listens on Tailscale Network Interface. Reverse proxies all private services.
	- Public: Listens on DO's Public IPv4 network interface. Reverse proxies all public-facing services.
- Terraform: Primary component to have IaC (Infra as Code). Modules to manage:
	- Cloudflare DNS Zone and Records
	- DO Droplet, Firewall rules, SSH Keys, Floating IPs etc.
	- Nomad Jobs. Used for running workloads after templating env variables, config files in Nomad job files.


## Complexity of Nomad vs Kubernetes

[![image](/images/k8s-meme.jpeg)](https://twitter.com/mrkaran_/status/1268762357355823104)


Nomad shines because it follows the UNIX philosophy of "Make each program do one thing well". To put simply, Nomad is _just_ a workload orchestrator. It only is concerned about things like Bin Packing, scheduling decisions.

If you're running heterogeneous workloads, running a server (or a set of servers) quickly becomes expensive. Hence orchestrators tend to make sense in this context. They tend to save costs by making it efficient to run a vast variety of workloads. This is all an orchestrator has to do really. 

Nomad doesn't interfere in your DNS setup, Service Discovery, secrets management mechanisms and pretty much anything else. If you read some of the posts at [Kubernetes Failure Stories](https://k8s.af/), the most common reason for outages is Networking (DNS, ndots etc). A lot of marketing around K8s never talks about these things.

I always maintain "Day 0 is easy, Day N is the real test of your skills". Anyone can deploy a workload to a K8s cluster, it's always the Day N operations which involve debugging networking drops, mysterious container restarts, proper resource allocations and other such complex issues that require real skills **and** effort. It's not as easy as `kubectl apply -f` and my primary gripe is with people who miss out on this in their "marketing" pitches (obvious!).

## When to use Nomad

Nomad hits the sweet spot of being operationally easy and functional. Nomad is a great choice if you want to:

- Run not just containers but other forms of workloads.
- Increase developer productivity by making it easier to deploy/onboard new services.
- Consistent experience of deployment by testing the deployments locally.
- (Not joking) You are tired of running Helm charts or writing large YAML manifests. The config syntax for Nomad jobs is human friendly and easy to grasp.

Nomad is available as a single binary. If you want to try it locally, all you need is `sudo nomad agent -dev` and you'll have a Nomad Server, Client running in dev mode along with a UI. This makes it easy for the developers to test out the deployments locally because there's very little configuration difference between this and production deployment. Not to forget it's super easy to self-host Nomad clusters. I'm yet to meet anyone who self hosts K8s clusters in production without a dedicated team babysitting it always.

Once you eliminate the "blackbox" components from your stack, life becomes easier for everyone.

## When to not use Nomad

- If you're relying on custom controllers and operators. [Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) is a new way of managing large complex distributed systems (like databases, job queues etc). There are a lot of community built operators which help in reducing the effort to run these services. However, all of these are tied deeply into the "Kubernetes" ecosystem. If you find yourself running any of such operators, it'll be tough (not impossible) to translate the same in Nomad ecosystem.

I _genuinely_ cannot think of any other reason to not use Nomad!

## Practical Scenarios

Since I migrated a couple of workloads from my DO docker containers setup to Nomad, I'd demonstrate a few use cases which might be helpful if you want to start migrating your services to Nomad

### Accessing a Web service with Reverse Proxy

Context: I'm running Caddy as a reverse proxy for all the services. Since we discussed earlier, Nomad **only** is concerned about scheduling, so how exactly do you do Service Discovery? You need Consul (or something like Consul, Nomad has no hard restrictions) to register a service name with it's IP Address. Here's how you can do that:

In the `.task` section of your Nomad job spec, you need to register the service name with the port you're registering and additional tags as metadata (optional):

```hcl
service {
  name = "gitea-web"
  tags = ["gitea", "web"]
  port = "http"
}
```

Nomad's [template](https://www.nomadproject.io/docs/job-specification/template) uses `consul-template` behind the scenes. This is a small utility which continuously watches for Consul/Vault keys and provides the ability to reload/restart your workloads if any of those keys change. It can also be used to _discover_ the address of the service registered in Consul. So here's an example of `Caddyfile` using Consul Template functions to pull the IP address of the upstream `gitea-web` service:

```hcl
git.mrkaran.dev {
    {{ range service "gitea-web" }}
    reverse_proxy {{ .Address }}:{{ .Port }}
    {{ end }}
}
```

When a job is submitted to Nomad, a rendered template is mounted inside the container. You can define actions on what to do when the values change. For eg on a redeployment of Gitea container, the address will most likely change. We'd like Caddy to automatically restart with the new address configured in the Caddyfile in that case:

```hcl
template {
  data = <<EOF
${caddyfile_public}
EOF

  destination = "configs/Caddyfile" # Rendered template.

  change_mode = "restart"
}
```

Using [`change_mode`](https://www.nomadproject.io/docs/job-specification/template#change_mode) we can either send a `signal` or restart the task altogether.

### Binding to different network interfaces

I run a public instance of Gitea but I wanted to restrict the SSH access only to my Tailscale network. Nomad has an interesting feature [`host_network`](https://www.nomadproject.io/docs/job-specification/network#host_network) which lets you bind different ports of a task on different network interfaces.

```hcl
network {
  port "http" {
    to = 3000
  }

  port "ssh" {
    to = 22

    # Need a static assignment for SSH ops.
    static = 4222

    # SSH port on the host only exposed to Tailscale IP.
    host_network = "tailscale"
  }
}
```

### Templating Env Variables

**NOTE**: This is **not** recommended for production.

Nomad doesn't have any templating functionalities, so all the config must be sourced from Consul and secrets should be sourced from Vault. However in the time constraint I had, I wanted to understand Nomad and Consul better and use Vault at a [later stage](https://github.com/mr-karan/hydra/blob/master/docs/SETUP.md#vault). I needed a way to interpolate the env variables. This is where Terraform comes into picture:

```
resource "nomad_job" "app" {
  jobspec = templatefile("${path.module}/conf/shynet.nomad", {
    shynet_django_secret_key   = var.shynet_django_secret_key,
    shynet_postgresql_password = var.shynet_postgresql_password
  })
  hcl2 {
    enabled = true
  }
}
```

We can pass the variables from Terraform (which can be sourced by `TF_VAR_` in your local env) to the Nomad job spec. Inside the job spec we can use `env` to make it available to our task:

```hcl
env {
  DB_PASSWORD              = "${shynet_postgresql_password}"
  DJANGO_SECRET_KEY        = "${shynet_django_secret_key}"
}
```

### Running a backup job on the host

I use `restic` to take periodic backups of my server and upload to Backblaze B2. Since Nomad supports running tasks as a different isolated environment (`chroot`) using `exec` driver and even without isolation using `raw_exec` driver, I wanted to give that a try. I've to resort using `raw_exec` driver here because `/data` file path on my host was not available to the chroot'ed environment.

```
job "restic" {
  datacenters = ["hydra"]
  type        = "batch"

  periodic {
    cron             = "0 3 * * *"
    time_zone        = "Asia/Kolkata"
    prohibit_overlap = true
  }
  ...
  task "backup" {
	  driver = "raw_exec"

	  config {
		# Since `/data` is owned by `root`, restic needs to be spawned as `root`. 

		# `raw_exec` spawns the process with which `nomad` client is running (`root` i.e.).
		command = "$${NOMAD_TASK_DIR}/restic_backup.sh"
	  }
  }
  ...
}
```

You can follow the rest of the config [here](https://github.com/mr-karan/hydra/blob/master/terraform/modules/restic/conf/restic.nomad).


## Scope of Improvements

Nomad has been an absolute joy to work with. However, I've spotted a few rough edge cases which I believe one should be aware of:

- `host_network` property sometimes gets ignored when doing a modification to `service`. I've opened an [issue](https://github.com/hashicorp/nomad/issues/10001) upstream but looks like other people are facing similar behaviours [here](https://github.com/hashicorp/nomad/issues/10016) and [here](https://github.com/hashicorp/nomad/issues/9006).
- `host_network` as of present [cannot](https://github.com/hashicorp/nomad/issues/8577) bind to a floating IP address (DigitalOcean/GCP etc). I've to resort to using my droplet's public IPv4 address for now. 
- I tried using Consul Connect (service mesh with mTLS) but looks like again because of `host_network`, I'm [unable](https://github.com/hashicorp/nomad/issues/9683) to use it.
- Nomad CLI can definitely be [improved](https://github.com/hashicorp/nomad/issues/9441) for a much more consistent experience. I particularly missed using `kubectl` when using `nomad`.

That apart, I ended up sending a [PR](https://github.com/hashicorp/nomad/pull/10026) to upstream addressing a CLI arg ordering issue.

### Gotchas:

- On a Nomad server _already_ bootstrapped, if you try changing `server.bind_addr`, it won't have any effect. I almost pulled my hair debugging this, ultimately deleting the `data_dir` of the server resolved the issue for me.
- I'm running DB _and_ the App together as a single "group" in my setup configs. Don't do this in production. Whenever you restart the job, the group will restart both the containers. The side effect of this is pretty interesting: Since we use Consul to fetch the DB Host, the app may start before the DB boots up _and_ registers its new address with Consul. I will fix the dependency in a future version but since I'm running fewer workloads and there are automatic retries, it's okay enough for me to keep it like this.

## Community

Nomad's community is pretty small compared to Kubernetes. However, the folks are super responsive on [Gitter](https://gitter.im/hashicorp-nomad/Lobby), [Discourse](https://discuss.hashicorp.com/) and Github Issues. A few noteworthy mentions:

- [@the-maldridge](https://github.com/the-maldridge) helped me with my doubts in Gitter.
- [@tgross](https://github.com/tgross) who is super responsive on Github issues and does an excellent job at housekeeping the issues.
- [@shantanugadgil](https://github.com/shantanugadgil) who is also pretty active in the community. 

Nomad's ecosystem is still in its nascent stage and I believe there are a lot of contribution opportunities for folks interested in Golang, Ops, Distributed Systems to contribute to Nomad. The codebase of Nomad is approachable and there are quite a few key areas which can be contributed to:

- Docs: More examples, practical use cases.
- Nomad Job files: There are many helm charts available to follow best practices. Something similar in Nomad will definitely be interesting.
- Nomad Gotchas: Since K8s is widely used and has a much larger adoption, it's only natural that the failure stories of K8s are highlighted a lot. Nomad being a pretty smaller community, we need more debugging and "things that went wrong" reference materials. You learn more from failures than 101 setup guides :)

## Final Thoughts

I think I'm _sold_ on Nomad. I've used Kubernetes in prod for 2 years but if you were to ask me to write a Deployment spec from scratch (without Googling/kubectl help) I won't be able to. After writing Nomad configs, I just can't think of the sheer amount of boilerplate that K8s requires to get an application running.

Nomad is also a simpler piece to keep in your tech stack. Sometimes it's best to keep things simple when you don't really achieve any benefits from the complexity.

Nomad offers _less_ than Kubernetes and it's a feature, not a bug.

Fin!

#### Discussions

- [HackerNews](https://news.ycombinator.com/item?id=26142005)
- [Lobster](https://lobste.rs/s/bybybm/running_nomad_for_home_server)
- [Twitter](https://twitter.com/mitchellh/status/1361361025568698368)
