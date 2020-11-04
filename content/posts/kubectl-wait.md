+++
title = "kubectl wait"
date = 2020-01-01T08:10:55+05:30
type = "post"
description = "A one-liner command to wait on K8s resources for changes"
in_search_index = true
[taxonomies]
tags = ["Kubernetes","Devops","CI/CD"]
+++

For the longest time I've had these commands in my `.gitlab-ci.yml` file for a K8s CD pipeline:

```sh
    ...
    - kubectl apply -k overlays/prod
    - echo "Waiting for 15 seconds for pods to be restarted" && sleep 15
    - kubectl get po
    ...
```

So, basically I apply the changes to cluster using `kubectl apply` and wait for arbitary decided time (15 seconds) to see the pod `status`, hoping by that time the new deployments would have been active and old pods would be deleted. As the traditional SRE saying goes _Hope is not a strategy_ this was clearly hacky and I knew it back then, just didn't priortise enough to find a replacement. Recently got to know about `kubectl wait` and woah, this is exactly what I needed. I can wait till either the condition is true or a timeout happens, whichever is earlier. This is so much better than the previous _hack_.

```
kubectl wait --for=condition=available --timeout=60s --all deployments
```

Here the `condition` depends on the resource you are selecting. You can see the values for `Conditions` using `kubectl describe <resource>`. For eg, for deployment and pods:

```bash
$ kc describe deployments/{deployment_name} | grep Conditions -A 5

Conditions:
  Type           Status  Reason
  ----           ------  ------
  Progressing    True    NewReplicaSetAvailable
  Available      True    MinimumReplicasAvailable
```

```bash
$ kc describe pods/{pod_name} | grep Conditions -A 5

Conditions:
  Type              Status
  Initialized       True
  Ready             True
  ContainersReady   True
  PodScheduled      True
```

So, now you'll set the value for `condition` according to your choice. This will be pretty useful in CI/CD pipelines. That's pretty much it.

---

Unrelated, but I thought about doing more such _short_ posts and be consistent with more of writing. If you liked the short and precise format or have any feedback on it, do reach out to me on [Twitter](https://twitter.com/@mrkaran_).

Happy New Year :)

Fin!
