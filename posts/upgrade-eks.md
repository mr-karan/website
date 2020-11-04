---
title: "Journey of upgrading AWS EKS cluster"
date: 2020-10-26T08:10:55+05:30
type: "post"
images: ["/images/ripe-measurement1.png"]
description: "The definitive guide to upgrade AWS EKS clusters and things you should keep in mind for a headache free upgrade"
tags:
  - Devops
  - Kubernetes
---

Out of all the major cloud offerings for a managed K8s clusters it's no mystery that AWS EKS is the most cumbersome of all when it comes to cluster upgrades. EKS has the concept of Cluster Plane and Node groups. It's only early in 2020 that AWS introduced Managed node groups, which means that unlike previously when you deployed an EKS cluster you aren't left with. But managed node groups still need to be manually updated if you bake your own AMIs. I mean I'm yet to come across anyone using EKS in prod with the default `sysctl` settings or custom packages. So "managed" and self created node groups are just about the same if you use your AMI. Anyway so the upgrade
