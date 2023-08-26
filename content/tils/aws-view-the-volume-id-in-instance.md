+++
title = "How to Identify the EBS Volume ID on an AWS EC2 Instance"
date = 2022-06-27
type = "til"
description = "A guide on how to determine the EBS Volume ID directly from within an EC2 instance."
in_search_index = true
[taxonomies]
tags = ["AWS", "EC2"]
+++

When managing EC2 instances with multiple EBS volumes, especially if they have similar sizes, it can be challenging to identify each one by its volume ID. 

There's a handy command for this:

```bash
lsblk -o +SERIAL
```

This command will display the EBS Volume ID for all attached volumes. It's especially useful when you need to modify or resize a specific volume without any mix-ups.
