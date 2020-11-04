+++
title = "Kubernetes cluster on RPi"
date = 2019-09-22T08:10:55+05:30
type = "post"
description = "Running k3s and self-hosting stuff on an RPi cluster"
in_search_index = true
[taxonomies]
tags = ["Networking", "Kubernetes", "Homeserver"]
+++

So, I got hold of 2 Raspberry Pi4 (still limited stocks in India) recently and wanted to build a Kubernetes cluster. Don't ask why cause that would be pointless. I've little experience with a managed Kubernetes workload (Amazon EKS, which btw deserves its post 😝) but never really played around any of the K8s internal stuff yet. In this post, I'll show you how I got a lightweight Kubernetes distro: K3s up and running.

[k3s](https://k3s.io/) is a pretty great Kubernetes distro which passes the K8s Conformance tests. On ARM architectures, you're pretty much resource-bounded and you want the resource footprint of your infra to be as minimal as possible. In k3s there are a few changes such as the persistent layer of K8s is replaced with SQLite instead of etcd, unusable (legacy/alpha) features of K8s are removed and cloud-provider plugins are not bundled (but can be installed separately). All of this together means just 40MB of a binary to run the cluster and ~250MB of memory usage on an idle cluster. Awesome, team [Rancher](http://rancher.com) :)

![image](/images/k3s-htop.png)

Automation is the key and even though I have just 2 nodes on RPi, I _Ansible-ized_ the setup which I am hoping would save time in future if I add more nodes to the setup.

## Hardware

- 1x [RPi4 4GB](https://www.crazypi.com/raspberry-pi-products/raspberry-pi-latest-model-boards/raspberry-pi-4-4gb-india) and 1x [RPi4 2GB](https://www.crazypi.com/raspberry-pi-products/raspberry-pi-latest-model-boards/raspberry-pi-4-2gb-india) variant
- 2x [Samsung EVO micro SD Card](https://www.amazon.in/gp/product/B06Y63B51W/ref=ppx_yo_dt_b_asin_title_o04_s00?ie=UTF8&psc=1)
- 2x [USBC Cables](https://www.amazon.in/gp/product/B01GGKYKQM/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
- 1x [Amker Power Port](https://www.amazon.in/gp/product/B00P933OJC/ref=ppx_yo_dt_b_asin_title_o06_s01?ie=UTF8&psc=1) (don't compromise on the power supply, give enough juice so RPi doesn't throttle)
- 1x [TP-Link Network Switch](https://www.amazon.in/gp/product/9800359788/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1) (my router has only 1 usable LAN port)
- 2x [CAT5 LAN cables](https://www.amazon.in/gp/product/B00GZLJ3EM/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) (keeping it basic, you can get fancy flat LAN cables if you wish to)

This is how the final setup looks like:

{{< tweet 1175659256764219392 >}}

### Setting up RPi

I downloaded [Raspbian Buster Lite](https://www.raspberrypi.org/downloads/raspbian/) because it's the easiest to setup. Next step is to flash the SD card and for that, I used [Etcher](https://www.balena.io/etcher/).

![image](/images/etcher.png)

To enable SSH access, you need to create an empty file `ssh` in the root volume.

```sh
sudo touch /boot/ssh
```

Once all sorted, we can use Ansible to set up the basic OS stuff, like changing the default password, enabling password-less SSH login, timezone & locale settings, changing hostname etc. I'll be sharing relevant Ansible snippets, if interested you can check out the complete playbook at [mr-karan/hydra repo](https://github.com/mr-karan/hydra).

We need to enable container features on the RPi so that `containerd` can run. Containers like Docker make use of `cgroups` (Linux kernel feature) which allows them to put resource limits on container processes like CPU and Memory. To enable `cgroups`, you need to edit `/boot/cmdline.txt`.

```yml
- name: Add cgroup directives to boot command line config
  lineinfile:
    path: /boot/cmdline.txt
    regexp: '((.)+?)(\scgroup_\w+=\w+)*$'
    line: '\1 cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory'
    backrefs: yes
```

Quick Tip: If you're going to use RPi as a headless server (not connecting with any monitor) you can reduce the GPU Memory to lowest possible (16M)

```yml
- name: Set GPU memory split to 16 MB
  lineinfile:
    path: /boot/config.txt
    line: "gpu_mem=16"
    create: yes
```

### Deploy K3s cluster

Next, we'll come to the actual stuff, where we'll download K3s binary and run as a systemd service. There's a handy [shell script](https://github.com/rancher/k3s#quick-start---install-script) to bootstrap the cluster provided by the Rancher team which setups the whole thing in one command. But if you wanna learn/play around I'd recommend you do things the hard way (it's not all that hard tho. ((twss!)).

```yml
- name: Download k3s binary armhf
  get_url:
    url: https://github.com/rancher/k3s/releases/download/{{ k3s_version }}/k3s-armhf
    dest: /usr/local/bin/k3s
    owner: root
    group: root
    mode: 755
  when: ( ansible_facts.architecture is search("arm") )
    and
    ( ansible_facts.userspace_bits == "32" )
```

On the worker node, the process is similar, except you have to run the K3s with `agent` compared to `server` argument in the control plane. Things get a bit interesting here though. You need to give the cluster server URL along with it's token in the command. A unique token is generated by the server at (`/var/lib/rancher/k3s/server/node-token`) which is used to join the worker nodes.

I did a bit of google-fu and got to know about this neat little Ansible module [`set_fact`](https://docs.ansible.com/ansible/latest/modules/set_fact_module.html) which lets you "store" a variable from one host and use it in a second host. Every Ansible host maintains a Python dict of "host facts". In the second node, I access the cluster's host fact `dict`, fetch the variable and use it in its systemd service template. Neat, ain't it? Ansible has so many modules, it is mind-boggling.

_Reading and storing the variable as a "host" fact_:

```yml
# on the cluster
- name: Read node-token from control node
  slurp:
    src: /var/lib/rancher/k3s/server/node-token
  register: node_token

- name: Store control node-token
  set_fact:
    k3s_cluster_token: "{{ node_token.content | b64decode | regex_replace('\n', '') }}"
```

_Using the variable from the server host, in a template on the agent host_:

```yml
# on the agent (vars.yml)
k3s_server_address: "{{ hostvars[groups['control'][0]].k3s_server_address }}"
k3s_cluster_token: "{{ hostvars[groups['control'][0]].k3s_cluster_token }}"
# use the value in a template
...
[Service]
ExecStart=/usr/local/bin/k3s agent --server {{ k3s_server_address }} --token {{ k3s_cluster_token }}
...
```

P.S. Shoutout to Ansible tho. It is one of my fav infra tooling available out there. It has some gotchas that you need to be aware of but by and large, the experience has been quite pleasant.

On the cluster, you should be able to see the nodes.

![image](/images/kube-nodes.png)

![image](https://media3.giphy.com/media/5GoVLqeAOo6PK/giphy.gif?cid=790b7611e1db0c17c4edaa597551fe748d1f3131429f424b&rid=giphy.gif)

### Team #SelfHost

I am planning to host Bitwarden, Gitea and a Nextcloud instance on this cluster. Also will be using this as a testbed to play around with K8s internals. Stay tuned as I explore more of this!

Cheers! :)
