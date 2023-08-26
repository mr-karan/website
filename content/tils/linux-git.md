+++
title = "Useful Git commands"
date = 2022-09-02
type = "til"
description = "A guide on how to use Git effectively in Linux, including how to set the editor, delete local and remote branches, and force merge a branch."
in_search_index = true
[taxonomies]
tags = ["Linux"]
+++

## Set the editor

```bash
git config --global core.editor "vim"
```

## Delete all local branches

```bash
git branch --merged | grep -v \* | xargs git branch -D
```

## Delete all branches except a few

```bash
git branch | grep -v "develop" | grep -v "master" | xargs git branch -D
```

## Delete a remote branch

```bash
git push origin :develop
```

## Force merge a branch

When you have too many conflicts while merging branch `feature` to `main`, use [this](https://stackoverflow.com/a/2862938/709452):

```bash
git checkout feature
git merge -s ours main
git push origin feature

git checkout main
git merge feature
git push origin main
```