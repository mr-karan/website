+++
title = "Resize PVC in Kubernetes"
date = 2020-01-14T08:10:55+05:30
type = "post"
description = "Easily expand Kubernetes Persistent Volumes"
in_search_index = true
[taxonomies]
tags= ["Kubernetes","Devops"]
+++

Well, the title is self explanatory so let's begin!

First off, we need to ensure that the `StorageClass` which was used to provision the PVC has the correct configuration. From the official [docs](https://kubernetes.io/docs/concepts/storage/persistent-volumes/):

> You can only expand a PVC if its storage class’s allowVolumeExpansion field is set to true.

So, let's inspect our storage class:

```sh
$ kubectl get sc # sc is short for storageclass
NAME            PROVISIONER             AGE
gp2 (default)   kubernetes.io/aws-ebs   8d

$ kubectl describe sc/gp2
# output redacted to focus only on the field we're concerned with
Name:            gp2
AllowVolumeExpansion:  True
```

If `AllowVolumeExpansion` is set to `True` you can skip the below step. If it's not true, you need edit the field `allowVolumeExpansion` as `true`:

```yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
  name: gp2
parameters:
  fsType: ext4
  type: gp2
provisioner: kubernetes.io/aws-ebs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

Once the `StorageClass` config is correct, all we need to do is update with the new size.

So, for example if size of the PVC was `15GB` orginally:

```yml
spec:
  resources:
    requests:
      storage: 15Gi
```

To update it to `30GB`, you simply need to edit `spec.resources.requests` field:

```yml
spec:
  resources:
    requests:
      storage: 30Gi
```

We now need to "apply" the updated PVC manifest.

```shell
$ kubectl apply -f pvc.yml
```

Let's take a look at the PVC:

```shell
$ kubectl describe pvc/myclaim
# output redacted for brevity
...
Conditions:
  Type                      Status  LastProbeTime                     LastTransitionTime                Reason  Message
  ----                      ------  -----------------                 ------------------                ------  -------
  FileSystemResizePending   True    Mon, 01 Jan 0001 00:00:00 +0000   Tue, 14 Jan 2020 20:52:21 +0530           Waiting for user to (re-)start a pod to finish file system resize of volume on node.
...
```

So, basically what `FileSystemResizePending` means is that while PVC is _in use_, we have to either restart or delete the underlying Pod using the PVC. At the time of writing this, `ExpandInUsePersistentVolumes` is still in [beta](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#resizing-an-in-use-persistentvolumeclaim) and has to be enabled as a feature gate. Sadly, EKS is still on `1.14` (while the world has moved to 1.17, such _sloooow_ release cycles!), so I couldn't enable this in my case.

Once the pod is restarted, the expanded disk is automagically available! Let's verify this:

```
kc get pvc/myclaim -o=jsonpath="{.status.capacity.storage}"
30Gi
```

Now, compare this with the standard way of resizing an EBS volume in EC2 instance. You need to first [modify](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/requesting-ebs-volume-modifications.html#modify-ebs-volume-cli) the volume size using AWS EBS API and then in the EC2 instance, use a combination of `growpart` and `resize2fs` to [extend](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/recognize-expanded-volume-linux.html) the resized volume. This sounds much more cumbersome than simply updating the storage field in PVC manifest!

Fin!
