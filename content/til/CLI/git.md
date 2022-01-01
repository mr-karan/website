+++
title = "Git"
date = 2021-11-13
type = "post"
in_search_index = true
[taxonomies]
til = ["CLI"]
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

```
git push origin :develop
```