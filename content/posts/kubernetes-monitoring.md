---
title: "Federated Prometheus monitoring of Kubernetes clusters"
date: 2021-04-15T10:57:55+05:30
type: "draft"
description: "Guide to setup a complete monitoring stack of all components required to build monitoring from ground up"
tags:
  - Kubernetes
  - Devops
  - Monitoring
---

So, off-late I've spent a considerable time on researching how to setup a Prometheus monitoring stack for Kubernetes clusters. Like every other thing in programming/ops, there are certain pros/cons to every solution you go ahead with. This post is about me explaining the rationale behind taking those decisions. A brief overview about the stack:

- kube-prometheus. The entire repo consists of manifests to deploy Prometheus, Alertmanager and Grafana in your cluster. Kubernetes Operators are basically a set of CRDs + custom application code written using Kubernetes SDKs to manage the lifecycle of application easily. They make routine tasks like adding new rules and reloading, service discovery across Pods, configuring Prometheus with a custom native Kubernetes resource manifest and much more. core-os/prometheus-operator is quite actively maintained by the community so it made sense to go ahead with this project and save me time from deploying manually.

- Victoria Metrics: This is the secret sauce of the stack. VM is used to aggregate and store all the time series data collected from all clusters. VM runs independtyel, outside of Kubernetes on a plain old EC2 instance. VM supports native PromQL, Prometheus compatibale datsopurce format (which means Grafana supports it out of the box), it's quite fast even with lot of metrics points.

- Central Grafana instance to view the metrics. This is also deployed out of Kubernetes, and connected to VM datasource.

- cAlert to fire off notifications. This is deployed in each cluster

So this is pretty much how the federated monitoring would look like.

I'd also like to mention that I did consider Prometheus Federation before Victoria Metrics. That unfortunaley had some shortcomings in my current use case:

- I could only scrape metrics from only one of the instance otherwise I would end up duplicating the data with different labels. I had to run an extra Promxy which is basically a proxy API to solve the same problem.
- Second grafana for more fine detailed metrics _or_ connect the Grafana directly to one of the prometheus instances

This whole setup where Grafana's data source is split also meant that doing complex queries which required data from cluster and out cluster was also difficult.

Next, I also did consider Thanos but running so many things and I didn't have that scale where Thanos would make sense. So, skip. Q

Ultimately due to these limitations, I decided to look out for other alternatives. I found Thanos which is a pretty pretty elabaroytive setup. Then I found Victoria Metrics and boy I was pleased.

- Use `remote_write`
- No statefulsets! Hurray
- Data is managed in one place
- All kinds of joins are possible
- Grafana connects directly. Imagine if you had 100 clusters, you would end up firewall rules with all of the clusters and expose the Prometheus endpoint which also mean setting up Ingress. Argh so messy.

- Single binary
- Support promQL

Victoria Metrics is a single binary, it supports promQL, really efficient compaction and benchmarks seems to be out of the world.

I'm running VM in production with no issues and it's highly recommended from my experience.

### Deploy kube-prometheus

I use the `kube-prometheus` stack which combines `prometheus-operator` along with a bunch of other utils like `Node Exporter`

### Setup Victoria Metrics

### Connect Grafana to VM

### cAlert to fire notifications
