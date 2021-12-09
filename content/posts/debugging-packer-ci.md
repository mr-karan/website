+++
title = "Debugging issues with Packer and Ansible in Docker"
date = 2021-11-16T00:00:00+05:30
type = "post"
description = "A brief summary and the fix for a weird permission issue I faced while running Packer with Ansible"
in_search_index = true
[taxonomies]
tags = ["Devops", "Ansible"]
+++

Today I faced an issue that questioned my sanity. Since I didn't find many "related" issues on StackOverflow/Google-fu except a lone GitHub thread where a kind stranger hinted at what could be the issue, I am writing about it here in the hopes (although I don't wish this torture on anyone) that it helps someone!

To give some context, I am running a [Gitlab CI](https://docs.gitlab.com/ee/ci/) job that bakes an [AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) using [Packer](https://www.packer.io/). Packer can use different kinds of provisioners to do configure stuff on the host and then prepare the image. I am using [Ansible provisioner](https://www.packer.io/docs/provisioners/ansible/ansible) to install and configure [Consul](https://www.consul.io/). At this point you may think this post is sponsored by Hashicorp by the sheer mention of all their products, but I assure you that is not the case.

Anyway, so this role works locally but it fails on the damn Gitlab CI. Classic case of [Works on my machine, Ops problem now](https://memegenerator.net/instance/64569365/disaster-girl-worked-fine-on-local-dev-ops-problem-now). These kinds of issues although are particularly exciting for me because they give me a chance to dig down deeper in the internals and slowly peel apart layers to figure out where the "drift" between local and CI is happening.

Here's the relevant Packer snippet (Oh and this week as I updated myself with new Packer releases, it's now possible to write Packer config with HCL and not just JSON anymore! Yayie. Again a reminder: not a sponsored post).

```hcl
build {
  sources = ["source.amazon-ebs.golden-ami"]
  provisioner "ansible" {
    playbook_file           = "${var.playbook_file}"
    extra_arguments         = ["--tags", "install", "-e", "ansible_python_interpreter=/usr/bin/python3"]
    ansible_env_vars        = ["ANSIBLE_LOCAL_TEMP=$HOME/.ansible/tmp", "ANSIBLE_REMOTE_TEMP=$HOME/.ansible/tmp"]
    galaxy_file             = "${var.galaxy_file}"
    inventory_file_template = "[consul_instances]\n{{ .HostAlias }} ansible_host={{ .Host }} ansible_user={{ .User }} ansible_port={{ .Port }}\n"
  }
}
```

Running `packer build` in CI results in a failure of a task defined in the Ansible playbook. The task simply creates a new group:

```yml
- name: Add Consul group
  group:
    name: "{{ consul_group }}"
    state: present
  when:
    - consul_manage_group | bool
```

[`group`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/group_module.html) runs `groupapp` command behind the scenes and you should be in the list of sudoers to actually create new groups. Since I already have `become: true` and `become_user: root` in my playbook that requirement is fulfilled. Moreover, this task runs just fine in the local as I mentioned above. While running in CI, I see the following error:

```
amazon-ebs.golden-ami: TASK [consul : Add Consul group] ***********************************************
amazon-ebs.golden-ami: fatal: [default]: FAILED! => {"changed": false, "msg": "groupadd: Permission denied.\ngroupadd: cannot lock /etc/group; try again later.\n", "name": "consul"}
```

Erhm, okayyy. That looks like a permission error. But why does this not happen in my local was the question eating me up.

Now was the time to start from the ground up and dissect different things going here. I will add a small hint though: The Gitlab CI runner is a [Docker-based](https://docs.gitlab.com/runner/executors/docker.html) runner. That means all the commands like `packer build` etc happen inside a Docker container. I am using `hashicorp/packer:light` image, which is an Alpine based image containing just the `packer` executable.

I tried to run the container locally with:

```sh
docker run -v `pwd`:/app --rm -it --entrypoint='' hashicorp/packer:light sh
```

And yes. When I ran `packer build`, I could replicate the issue here! But wait. More questions than answers. Ansible would run this `groupadd` command on the remote host, right? Why does Ansible care if it's inside a container or not? So, I created a really simple playbook to reproduce this further.

```
- name: Assemble Consul cluster
  hosts: localhost
  any_errors_fatal: true
  become: true
  become_user: root
  tasks:
    - name: Add Consul group
      group:
        name: debug_consul
        state: present
```

I ran this `ansible-playbook test.yml` inside the container and... it worked! Okay, now it's becoming clear. We aren't executing `ansible-playbook` directly, it's being wrapped by Packer. So this is clearly getting messed up by Packer. This time I did find a [GitHub issue](https://github.com/hashicorp/packer/issues/5421) where people were asking about similar issues and this person described it well:

![image](/images/packer_root_issue.png)

I opened [Packer docs](https://www.packer.io/docs/provisioners/ansible/ansible#become-yes) again and that's when I read this:

> We recommend against running Packer as root; if you do then you won't be able to successfully run your Ansible playbook as root; become: yes will fail.

WTF!!! This was right there in the docs, hiding in plain sight. Sheesh!

Okay, so I can not run my playbook with `become: true` with the packer Image (which uses root user). Time to fix that by building a custom image. That is because Gitlab CI [won't let me change the user](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/2750) without hacking stuff. And a custom image also allows me to ditch Alpine for Ubuntu, which is what I prefer.

```
FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    python3 \
    git \
    curl \
    unzip \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -o packer.zip https://releases.hashicorp.com/packer/1.7.8/packer_1.7.8_linux_amd64.zip
RUN unzip packer.zip
RUN mv packer /usr/local/bin

RUN pip3 install ansible

RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 ubuntu
USER ubuntu

WORKDIR /tmp

ENV PATH="$HOME/.local/bin:$PATH"

WORKDIR /app
```

Using this custom image, the packer build worked just fine. Fun day indeed (/s).

Fin!
