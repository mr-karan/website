+++
title = "Executing Commands as Different Users in Bash"
date = 2022-06-12
type = "til"
description = "A brief guide on how to execute commands as different users in a bash shell using sudo."
in_search_index = true
[taxonomies]
tags = ["Shell"]
+++

Here's an example of running `echo` but as a `consul` user:

```bash
sudo -H -u consul bash -c 'echo "I am $USER, with uid $UID"' 
```