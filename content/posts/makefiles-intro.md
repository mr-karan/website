+++
title = "Makefile for Golang projects"
date = 2018-10-11T18:10:55+05:30
type = "post"
description = "Using Makefile to Automate your Build Process"
in_search_index = true
[taxonomies]
tags = ["Golang"]
+++

Makefile is an awesome tool to group together a bunch of different rules and automate your build process. Makefile is used by `make` which is essentially a file generator tool. It is generally used to compile and build programs from source by following `rules` listed in the Makefile. People use Makefile for a lot of different purposes as well, for example converting `md` to `html` and publish these files to the web server.

Every makefile you see, is composed of rules. A `rule` is declaration of a `target` and the commands to be executed to generate the target. A target can be a file or an action to be performed (more on that later).

This is how a rule looks like in a Makefile

```bash
target: dependencies
    recipe
```

When you run `make target`, `make` searches for the rule which begins with this `target` and executes the dependecies (if required). It then runs a bunch of commands which are listed in the recipe. An important thing to understand here is that `make` tracks the dependencies by their last modified time. So if the dependencies haven't changed, then make will complain with `make: 'target' is up to date.`

Enough of theory, let's get our feet wet by writing our first Makefile. One important thing about `Makefile` is that you need to use `tabs` and not `spaces`. It is one of the rare `*nix` programs which is whitespace aware and this has been mentioned in [The Unix-Haters Handbook](https://en.wikipedia.org/wiki/The_Unix-Haters_Handbook) as well.

To begin with, let's write a simple rule which removes any tempory object files using `go clean` and previous binary file using good ol `rm`:

```bash
clean:
	go clean
	rm -f sample.bin
```

The `target` here is `clean`. There is something special going on here though. Imagine we have a file called `clean` in our source directory? Let us try to run `make clean` now
Our directory structure:.

```
├── Makefile
├── clean
└── sample.bin
```

On running `make clean`:

```
make: `clean' is up to date.
```

Every target in Makefile by default is a `file target`. In our case `clean` is a file target and `make` tries to build this file `clean` but since we already have a file with the same name `clean` in our directory, `make` is complaining there's nothing to do.

Moreover, in this case our rule is more of an `action` rather than building files. So for all such scenarios, `make` provides an easy way where we can instruct it to just run the rule and ignore any filename in our directory. This is called a `PHONY` target which is a special kind of target. `PHONY` is just a way in `make` to forcefully run a target and not care about generating files. Our aim with this rule is to run 2 commands and that's about it. So this is the perfect example for using `PHONY`.
We can add `.PHONY` target to our Makefile simply by this line:

```bash
.PHONY : clean

clean:
	go clean
	rm -f sample.bin

```

Now when we run `make clean` we get our expected output

```
go clean
rm -f sample.bin
```

Let us extend our Makefile to do some common tasks:

```bash
.PHONY : build run fresh test clean

test:
	go test

build:
	go build

run:
	./sample.bin

clean:
	go clean
	rm -f sample.bin
```

If you have worked on any Golang project, these are very trivial actions on any Golang project. You will soon realise the power of Makefile when you have to do these steps repeatedly. Some people might argue then you can use aliases or simple shell scripts for the same. I vehemently disagree with that. Reason being, `make` is a much more powerful tool than just running commands. `make` has support for dependency tracking and it will only rebuild whatever is required. If you are working on a huge project where the build times are to the tune of hours, you will soon realise why shell scripts are inferior. Ofcourse, someone can point that they can write a shell script to do even that, by fetching the last modified time but why do the extra work when there's an already existing tried and tested tool? `make` also has support for parallel task execution, so you can just pass the flag `-j {num}` to `make` and it will run these {num} jobs parallely. All these benefits will be apparent for larger projects, but it is a good habit to write Makefile even for smaller projects.

![#1 Excuse](https://imgs.xkcd.com/comics/compiling.png "Look Ma! Code is compiling")

We will now make our Makefile a bit more sophisticated and introduce variables. If you want to custom name your binary, or [inject variables at compile time](https://blog.cloudflare.com/setting-go-variables-at-compile-time/), you can declare these variables, for example:

```bash
BIN := my-awesome-pro.bin
HASH := $(shell git rev-parse --short HEAD)
COMMIT_DATE := $(shell git show -s --format=%ci ${HASH})
BUILD_DATE := $(shell date '+%Y-%m-%d %H:%M:%S')
VERSION := ${HASH} (${COMMIT_DATE})
```

We can modify our Makefile to use these variables:

```bash
build:
	go build -o ${BIN} -ldflags="-X 'main.buildVersion=${VERSION}' -X 'main.buildDate=${BUILD_DATE}'"

run:
	./${BIN}

test:
	go test

clean:
	go clean
	rm -f ${BIN}
```

We can auto version our builds and pass variables during the build time with go linker tool, on passing the `-X` flag. That's really neat, now whenever we do a `make build` we get new version of the build automagically.

So now we have a working Makefile which helps us with trivial things, but everytime if we need to change something in our program and check, we still need to do these steps manually: `make clean`, `make build` and `make run`. Won't it be awesome if we could tell Makefile to do all this with just one command? Programmers are lazy creatures after all <i class="em em-smiley"></i>.

In the beginning we saw a target is composed of recipe and dependencies. So we can just create a new `PHONY` target with all these dependencies and any recipe if we want optionally.

```bash
fresh: clean build run
```

We created a new `target` which depends on `clean` to run first, then `build` and finally `run`. So everytime if we make some change in our Go program, all we need to run is `make fresh`. Awesome, isn't it?

We will finally add our last target which is a highly opinionated way of generating binaries for different OS and architectures.

```bash
prod:
	goreleaser --rm-dist --snapshot
	cp dist/linux_amd64/${BIN}-linux.bin .
	rm -rf dist
```

This target runs `goreleaser` which is a build automation tool. It then copies the required linux binary to the source directory and removes all the other junk.

You can even extend your Makefile to commit files to a repo, and rsync these binaries to the production server or initiate your CI/CD build process. The reason I like Makefile is because it serves as a living documentation for your project on how to build/deploy the project making it easier for new contributors to get started.

##### Some additional information

- If you run `make` without passing any target name, `make` will run the first target present in the Makefile. To override this, you should set `.DEFAULT_GOAL` setting and [override the target](https://www.gnu.org/software/make/manual/html_node/Special-Variables.html#Special-Variables) which you want to make as default.

- `.PHONY` is just one way to tell `make` that it is a special kind of target, you can also do the same by creating a target without any recipe. Read [this](https://www.gnu.org/software/make/manual/html_node/Force-Targets.html#Force-Targets) to know more.

To know more about `Makefile`, you can read the manual [here](https://www.gnu.org/software/make/manual/make.html)

I hope you now appreciate `Makefile` and try it out in your next project. I'd love feedback on this blog post, do reach me out at [twitter](https://twitter.com/mrkaran_) or [email](mailto:karansharma1295@gmail.com)

Fin!
