+++
title = "Don't use which"
date = 2022-08-08T00:00:00+05:30
type = "post"
description = "Problems with which and its alternatives."
in_search_index = true
[taxonomies]
tags= ["Linux"]
+++

`which` is a non-standard/non-POSIX compliant program. I faced many issues getting `which` to work in a chroot environment (Nomad).

So basically, `which` is a simple shell script program to find out the dependency by searching the `$PATH` (which is what makes it less deterministic). It's also somehow symlinked 3 levels deep in Debian:

```sh
$ ls -laht /usr/bin/which
lrwxrwxrwx 1 root root 23 Apr 26 22:25 /usr/bin/which -> /etc/alternatives/which
$ ls -laht /etc/alternatives/which
lrwxrwxrwx 1 root root 26 Apr 26 22:25 /etc/alternatives/which -> /usr/bin/which.debianutils
```

Now, notice this:

```sh
$ which ls
ls: aliased to ls --color=tty

$ /usr/bin/which.debianutils ls
/usr/bin/ls
```

Both are the same programs. However, why is the output different? This is because `which` is apparently a shell built-in `zsh`, that is why:

```sh
# zsh
which which
which: shell built-in command

# bash
which which
/usr/bin/which
```

The inconsistency happens because `zsh` treats `which` as a shell built-in when it's apparently not one.

[This](https://lwn.net/Articles/874049/) article has some more details on why `which` is _bad_ and how the Debian team is slowly deprecating it from being a part of debianutils anymore.

When I invoked `which` from inside a Nomad chroot, it complained that I didn't have `/bin/sh` (because I was using a custom chroot mount). I started looking hard for alternatives because this silly utility already wasted too much of my time.

## What to use

Use `command -v`. It's a shell built-in, so it avoids a dependency on an external binary (unlike `which`).

### Usage example:

```bash
if ! command -v aws > /dev/null; then
        echo "Can't find 'aws' executable. Aborted."
        exit 1
fi
```

## References

I found the following posts while digging `which` and its alternatives.

- [which-not-posix](https://hynek.me/til/which-not-posix/)
- [why-not-use-which-what-to-use-then](https://unix.stackexchange.com/questions/85249/why-not-use-which-what-to-use-then)

Fin
