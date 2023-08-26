+++
title = "Generating Random Strings in Shell Scripts"
date = 2022-06-21
type = "til"
description = "Learn how to generate random strings in Shell, a useful technique for creating random passwords, unique identifiers, and more."
in_search_index = true
[taxonomies]
tags = ["Shell"]
+++

Generating random strings in Shell can be useful in various scenarios such as creating random passwords, unique identifiers, and more. Here are a couple of methods you can use:

1. Using `tr` and `/dev/urandom`:
   ```shell
   tr -dc A-Za-z0-9 </dev/urandom | head -c 13 ; echo ''
   ```
   This command will generate a 13-character random string using alphanumeric characters.

2. Using `openssl`:
   ```shell
   openssl rand -base64 12
   ```
   This command will generate a random string in base64 format.

Remember to replace the numbers in these commands with the length of the string you want to generate.