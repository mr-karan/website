+++
date = "2023-02-15T07:29:53+00:00"
description = "A quick introduction to slog, the structured logging library for Go."
in_search_index = true
og_preview_img = "https://images.unsplash.com/photo-1526423007471-5d86aebf3d5c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxMTc3M3wwfDF8c2VhcmNofDZ8fGxvZ3xlbnwwfHx8fDE2NzY0NDY2MzI&ixlib=rb-4.0.3&q=80&w=2000"
slug = "structured-logging-in-go-with-slog"
title = "Structured logging in Go with slog"
type = "post"

[taxonomies]
  tags = ["golang"]

+++


A few months ago, a [proposal](https://github.com/golang/go/issues/56345) for adding a structured logging library in Go was introduced by [Jonathan Amsterdam](https://github.com/jba). At present, Go has a minimal and bare-bones log package which works all right for basic use cases. However, the current library has a few shortcomings that this proposal aims to solve:

* Emitting logs with different severity/levels
* Structured output: Makes parsing of logs harder
* Logging a set of common fields/attributes
* Difficult to have a log object inside libraries as each service could have its log implementation.

As a result, many code bases have their wrappers around the log package. Additionally, there are plenty of 3rd party libraries to choose from - including [logf](https://github.com/zerodha/logf) (which my work colleagues and I built at Zerodha).

This article is about how to get started with [slog](https://pkg.go.dev/golang.org/x/exp/slog) for logging in Go applications.

{% admonition(kind="Note") %}
Since slog is currently in the proposal state and hasn't yet merged in the official library, the API could change in future.
{% end %}

## Architecture of slog

At a higher level, slog contains three main entities:

* **Logger**: The user-facing API for interacting with slog. All the public methods are defined on the Logger object.
* **Record**: Contains information about the log event itself. A standard record will have timestamp, level and message fields as default. Additional attributes and metadata like caller info can be added to the Record.
* **Handlers**: A handler is an _interface_ implementation. The Logger object passes the Record to a handler, and the handler can choose whatever it wants to do with the Record. This is a common approach in Go libraries, where a "provider" can be abstracted in handling that task. Currently, slog ships with two handlers: JSON and [logfmt](https://brandur.org/logfmt). Some projects have also created handlers for zap/logrus (popular 3rd party libraries).

### Initialization

This snippet initializes a Text Handler, which produces `logfmt` format messages on `os.Stdout`.

```go
package main

import (
	"os"

	"golang.org/x/exp/slog"
)

func main() {
	log := slog.New(slog.NewTextHandler(os.Stdout))
	log.Info("Hello world")

	fakeErr := os.ErrNotExist
	log.Error("something went wrong", fakeErr, "file", "/tmp/abc.txt")
}

```

Log output:

```bash
time=2023-02-15T19:58:10.615+05:30 level=INFO msg="Hello world"
time=2023-02-15T19:58:10.615+05:30 level=ERROR msg="something went wrong" file=/tmp/abc.txt err="file does not exist"
```

### Customizing

You'll notice that the caller information isn't exposed by default. The reason could be that finding the stack trace of the calling line is a bit expensive operation. However, for libraries/apps which need it can do that by customizing the handler:

```Go
func main() {
	handler := slog.HandlerOptions{AddSource: true}
	log := slog.New(handler.NewTextHandler(os.Stdout))

	log.Info("Hello world")
}

```

Log Output:

```bash
time=2023-02-15T12:17:53.742+05:30 level=INFO source=/home/karan/Code/Personal/slog-examples/main.go:14 msg="Hello world"
```

### Attributes

Sometimes, it's helpful to append specific metadata to each log line which will help in aggregating/filtering with a central log-collecting agent. E.g., you can export a component key for each sub-service of your primary application.

```Go
func main() {
	log := slog.New(slog.NewTextHandler(os.Stdout)).With("component", "demo")
	log.Info("Hello world")
}

```

Log Output:

```bash
time=2023-02-15T12:21:50.231+05:30 level=INFO msg="Hello world" component=demo
```

### Nested Keys

So far, we've seen flat keys in the log message. It may be helpful to group together specific keys together and form a nested object. In JSON, that would mean a top-level object with different fields inside. However, in `logfmt`, it would-be `parent.child` format.To use nested keys, `slog.Group` can be used. This example uses `http` as the top-level key, and all its associated fields will be nested inside.

```Go
	log.Info("Hello world", slog.Group("http",
		slog.String("method", "GET"),
		slog.Int("status", 200),
		slog.Duration("duration", 250),
		slog.String("method", "GET"),
		slog.String("path", "/api/health")))

```

```bash
time=2023-02-15T12:30:43.130+05:30 level=INFO msg="Hello world" component=demo http.method=GET http.status=200 http.duration=250ns http.method=GET http.path=/api/health
```

### Configurable Handlers

JSON logs are daunting and tedious to read when locally developing applications. However, it's a great fit for machine parsing of the logs. `logfmt` hits the sweet spot for being machine parseable and human-readable.However, thanks to the powerful "interface" implementation approach, it's easy to switch to any handler via user-configurable methods (like config files/env variables):

```go
package main

import (
	"os"

	"golang.org/x/exp/slog"
)

func main() {
	var (
		env     = os.Getenv("APP_ENV")
		handler slog.Handler
	)

	switch env {
	case "production":
		handler = slog.NewJSONHandler(os.Stdout)
	default:
		handler = slog.NewTextHandler(os.Stdout)
	}

	log := slog.New(handler)
	log.Info("Hello world")
}

```

```bash
$ go run main.go
time=2023-02-15T12:39:45.543+05:30 level=INFO msg="Hello world"
$ APP_ENV=production go run main.go
{"time":"2023-02-15T12:39:53.523477544+05:30","level":"INFO","msg":"Hello world"}

```

## Summary

`slog` is an excellent proposal, and it's high time Go gets its official structured logging library. The API is designed to be easy to use, and a clear path is given for users wanting high-performance/zero-allocs by creating their handlers and making these performance improvements.

Fin

