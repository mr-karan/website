+++
title = "Different usecases in Ansible"
date = 2021-06-09
type = "post"
in_search_index = true
[taxonomies]
til = ["Ansible"]
+++

## Assert a list of variables

```yml
---
- name: assert if all template variables are present
  assert:
    that:
      - "{{item}} is defined"
      - "{{item}} | length > 0"
    quiet: false
  with_items:
    - my_var
    - another_var
  no_log: true
```

## Execute a task before executing a role

```yml
- hosts: "my_server"
  become: yes
  # Assert if variables are present.
  pre_tasks:
    - import_tasks: ../tasks/assert.yml
  roles:
    - role: nginx
```

## Wait for apt-get lock before installing packages

```yml
# https://github.com/ansible/ansible/issues/51663#issuecomment-752286191
# A common issue, particularly during early boot or at specific clock times
# is that apt will be locked by another process, perhaps trying to autoupdate
# or just a race condition on a thread. This work-around (which can also be
# applied to any of the above statements) ensures that if there is a lock file
# engaged, which is trapped by the `msg` value, triggers a repeat until the
# lock file is released.
- name: Install OS dependencies
  apt:
    name: "{{ consul_os_packages }}"
    state: present
  register: apt_action
  retries: 100
  until: apt_action is success or ('Failed to lock apt for exclusive operation' not in apt_action.msg and '/var/lib/dpkg/lock' not in apt_action.msg)

```