+++
date = "2023-07-23T05:34:47+00:00"
description = "Unravel why Nomad can handle everything that K8s can and more, based on personal experience"
in_search_index = true
og_preview_img = "https://images.unsplash.com/photo-1604948501466-4e9c339b9c24?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wxMTc3M3wwfDF8c2VhcmNofDJ8fGJhdHRsZXxlbnwwfHx8fDE2OTAwMzA4MDN8MA&ixlib=rb-4.0.3&q=80&w=2000"
slug = "nomad-k8s-showdown"
title = "Nomad can do everything that K8s can"
type = "post"
[taxonomies]
  tags = ["nomad", "kubernetes"]
+++


This blog post is ignited by the following [Twitter exchange](https://twitter.com/ibuildthecloud/status/1682800502738931712):

![](/images/nomad-k8s-showdown-1.png)

I don't take the accusation of _unsubstantiated_ argument, especially on a technical topic lightly. I firmly believe in substantiated arguments and hence, here I am, elaborating on my stance. If found mistaken, I am open to corrections and revise my stance.

### Some Historical Context

In my professional capacity, I have run and managed several K8s clusters (using AWS EKS) for our entire team of devs (_been there done that_). The most complex piece of our otherwise simple and clean stack was K8s and we'd been longing to find a better replacement. None of us knew whether that would be Nomad or anything else. But we took the chance and we have reached a stage where we can objectively argue that, for our specific workloads, Nomad has proven to be a superior tool compared to K8s.

## Building with Nomad

Nomad presents a fundamental building block approach to designing your own services. It used to be true that Nomad was primarily a scheduler, and for serious production workloads, you had to rely on Consul for service discovery and Vault for secret management. However, this scenario has changed as Nomad now seamlessly integrates these features, making them first-class citizens in its environment. Our team replaced our HashiCorp stack with just Nomad, and we never felt constrained in terms of what we could accomplish with Consul/Vault. While these tools still hold relevance for larger clusters managed by numerous teams, they are not necessary for our use case.

## Deconstructing Infrastructure

Kubernetes employs a declarative state for every operation in the cluster, essentially operating as a reconciliation mechanism to keep everything in check. In contrast, Nomad requires dealing with fewer components, making it appear lacking compared to K8s's concept of everything being a "resource." However, that is far from the truth.

* **Ingress**: We run a set of HAProxy on a few nodes which act as "L7 LBs". Configured with Nomad services, they can do the routing based on Host headers.
* **DNS**: To provide external access to a service without using a proxy, we developed a [tool](https://github.com/mr-karan/nomad-external-dns) that scans all services registered in the cluster and creates a corresponding DNS record on AWS Route53.
* **Monitoring**: Ah my fav. You wanna monitor your K8s cluster. Sure, here's [kube-prometheus](https://github.com/prometheus-operator/kube-prometheus), [prometheus-operator](https://github.com/prometheus-operator/prometheus-operator), [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics). Choices, choices. Enough to confuse you for days. Anyone who's ever deployed any of these, tell me why this thing needs such a monstrosity setup of CRDs and operators. Monitoring Nomad is such a breeze, [3 lines of HCL](https://developer.hashicorp.com/nomad/docs/configuration/telemetry) config and done.
* **Statefulsets**: It's 2023 and the irony is rich - the recommended way to run a database inside K8s is... not to run it inside K8s at all. In Nomad, we run a bunch of EC2 instances and tag them as `db` nodes. The DBs don't float around as containers to random nodes. And there's no CSI plugin reaching for a storage disk in AZ-1 when the node is basking in AZ-2. Running a DB on Nomad feels refreshingly like running it on an unadorned EC2 instance.
* **Autoscale**: All our client nodes (except for the `db` nodes) are ephemeral and part of AWS's Auto Scaling Groups (ASGs). We use ASG rules for the horizontal scaling of the cluster. While Nomad does have its own autoscale, our preference is to run large instances dedicated to specific workloads, avoiding a mix of different workloads on the same machine.

## Over abstraction of Kubernetes

One of my primary critiques of K8s is its hidden complexities. While these abstractions might simplify things on the surface, debugging becomes a nightmare when issues arise. Even after three years of managing K8s clusters, I've never felt confident dealing with databases or handling complex networking problems involving dropped packets.

You might argue that it's about technical chops, which I won't disagree with - but then do you want to add value to the business by getting shit done or do you want to be the resident K8s whiz at your organization?

Consider this: How many people do you know who run their own K8s clusters? Even the K8s experts themselves preach about running prod clusters on EKS/GKE etc. How many fully leverage all that K8s has to offer? How many are even aware of all the network routing intricacies managed by kube-proxy? If these queries stir up clouds of uncertainty, it's possible you're sipping the Kubernetes Kool-Aid without truly comprehending the recipe, much like I found myself doing at one point

## Nomad: Not Perfect, But Simpler

Now, if you're under the impression that I'm singing unabashed praises for Nomad, let me clarify - Nomad has its share of challenges. I've personally encountered and reported several. However, the crucial difference lies in Nomad's lesser degree of abstraction, allowing for a comprehensive understanding of its internals. For instance, we encountered [service reconciliation issues](https://github.com/hashicorp/nomad/issues/16762) with a particular Nomad version. However, we could query the APIs, identify the problem, and write a bash script to resolve and reconcile it. It wouldn't have been possible when there are too many moving parts in the system and we don't know where to even begin debugging.

The [YAML hell](https://noyaml.com/) is all too well known to all of us. In K8s, writing job manifests required a lot of effort (by the developers who don't work with K8s all day) and were very complex to understand. It felt "too verbose" and involved copy pasting large blocks from the docs and trying to make things work. Compare that to HCL, it feels much nicer to read and shorter. Things are more straightforward to understand.

I've not even touched upon the nice-ities on Nomad yet. Like better humanly understandable ACLs? Cleaner and simpler job spec, which defines the entire job in one file? A UI which actually shows everything about your cluster, nodes, and jobs? Not restricting your workloads to be run as Docker containers? A single binary which powers all of this?

The central question this post aims to raise is: What can K8s do that Nomads can't, especially considering the features people truly need? My perspectives are informed not only by my organization but also through interactions with several other organizations at various meetups and conferences. Yet, I have rarely encountered a use case that could only be managed by K8s. While Nomad isn't a panacea for all issues, it's certainly worth a try. Reducing the complexity of your tech stack can prove beneficial for your applications and, most importantly, your developers.

At this point, K8s enjoys immense industry-wide support, while Nomad remains the unassuming newcomer. This contrast is not a negative aspect, per se. Large organizations often gravitate towards complexity and the opportunity to engage more engineers. However, if simplicity were the primary goal, the prevailing sense of overwhelming complexity in the infrastructure and operations domain wouldn't be as pervasive.

## Conclusion

I hope my arguments provide a more comprehensive perspective and address the earlier critique of being unsubstantiated.

## Update

{% admonition(kind="Info") %}
Darren has responded to this blog post. You can read the response on [Twitter](https://twitter.com/ibuildthecloud/status/1682992374979629057).
{% end %}

Fin!
