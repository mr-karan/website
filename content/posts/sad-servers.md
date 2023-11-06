+++
title = "Making sad servers happy"
date = 2023-11-06
type = "post"
description = "Tackling the unique challenges on sadservers.com. I record my solutions and share them in video format."
in_search_index = true
[taxonomies]
tags= ["Linux", "Devops"]
+++

## Introduction to SadServers

Recently, I stumbled upon [sadservers](sadservers.com), a platform described as "Like LeetCode for Linux". The premise is: you are given access to a full remote Linux server with a pre-configured problem. Your mission is to diagnose and fix the issues in a fixed time window.

With the goal of documenting my journey through these challenges and sharing the knowledge gained, I decided to not only tackle these puzzles but also to record my solutions in a video format. The format is twofold in its purpose: it allows me to reflect on my problem-solving approach and provides a resource for others who may encounter similar problems, whether in real-world scenarios or in preparation for an SRE/DevOps interview.

## The Learning Curve

Each server presented a different issue, from misconfigured network settings to services failing to start, from permission issues to resource overutilization. One server, for instance, had a failing database service because of a disk full partition. The cause? Stale backup files. Another had a web server throwing errors because of incorrect file permissions.

## Recording the Solutions

The video recordings start with an introduction to the problem and my initial thoughts. Viewers can see my screen as I work through the issue, making the troubleshooting process transparent and educational. The commentary explains my thought process, the tools/CLI utilities used, and the solutions applied.

### Part 1

<iframe width="560" height="315" src="https://www.youtube.com/embed/vdR8-ubkpRU?si=GGusRmnqk8bqKoCW" title="Making sad servers happy - Part 1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

### Part 2

<iframe width="560" height="315" src="https://www.youtube.com/embed/b-VFnaX78xY?si=Ql0zvph3p-U5wzwE" title="Making sad servers happy - Part 2" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

### Part 3

<iframe width="560" height="315" src="https://www.youtube.com/embed/-42S4xcim8Y?si=n1s7KHyZluyf4TLc" title="Making sad servers happy - Part 3" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Conclusion

For those looking to enhance their Linux troubleshooting skills, sadservers.com is a gold mine. It’s an excellent preparation ground for anyone aiming to step into the SRE/DevOps field or wanting to keep their skills sharp.

As I continue to record and share these troubleshooting escapades, I invite you to subscribe, comment with your insights, or even suggest what types of challenges you'd like to see addressed next.
