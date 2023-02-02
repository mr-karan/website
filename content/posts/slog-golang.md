+++
title = "Structured logging in Go with slog"
date = 2023-01-26T00:00:00+05:30
draft = true
type = "post"
description = "A quick introduction to slog, the official structured logging library for Go"
in_search_index = true
[taxonomies]
tags = ["golang"]
+++

A few months ago, a proposal for introducing a structred logging library in Golang was proposed. Go has a very minimal and barebones and logging `log` package. However, it's missing out on some features which makes log aggregation and parsing easier. The standard library doesn't have support for:

- Emitting logs with different serverity/levels
- Structured output: Makes parsing of logs harder
- Logging a set of common fields/attributes
- Difficult to have a `log` object inside libraries, because each service could have their own log implementation which isn't comptaible with so many libraries.

As a result, a lot of code-bases have their own wrappers around the log package. Additionally, There are plenty of 3rd party libraries to choose from - including [`logf`](https://github.com/zerodha/logf) that me and my work colleagues built at Zerodha.

This article is about how to get started with [`slog`](https://pkg.go.dev/golang.org/x/exp/slog) for logging in Go applications.

## Creating the logger

`slog`

slog utilises the concept of "pluggable" backends. Currently it supports JSON and logfmt (`key=val` style) outputs by customising the "handler".

The default handler is TextHandler. Here's how to initialise it:

package main

import (
	"os"

	"golang.org/x/exp/slog"
)

func main() {
	log := slog.New(slog.NewTextHandler(os.Stdout))
	log.Info("trying out new logger")
}

This produces the following output:

time=2023-01-24T16:55:31.526+05:30 level=INFO msg="trying out new logger"

Similarly, log messages for different levels can be generated.

log.Error("something went wrong", os.ErrNotExist, "file", "main.go")

Output:

time=2023-01-24T17:12:34.751+05:30 level=ERROR msg="something went wrong" file=main.go err="file does not exist"

NOTE: slog currently doesn't support TRACE and FATAL. I couldn't find any reason why fatal is missing in the design doc, because it's a common pattern in many "initialisers" to fail if something fails to initialise with a helpful log message.
Custom handler options

We can customise a few options to the handler. For eg, I find adding the caller information to be useful in logs.

handler := slog.HandlerOptions{
	AddSource: true,
}
log := slog.New(handler.NewTextHandler(os.Stdout))
log.Info("trying out new logger")

time=2023-01-24T17:00:51.541+05:30 level=INFO source=/home/karan/Code/Personal/slog-examples/main.go:14 msg="trying out new logger"

Common Attributes

It's useful to append certain metadata to each log. Sometimes you may want to push the logs to a central log collecting agent and if it contains some common fields like service/component, it helps to distinguish the logs.

log := slog.New(handler.NewTextHandler(os.Stdout).WithAttrs([]slog.Attr{slog.String("version", "4.2.0"), slog.String("component", "demo")}))
log.Info("trying out new logger")

Output:

time=2023-01-24T17:04:50.482+05:30 level=INFO source=/home/karan/Code/Personal/slog-examples/main.go:14 msg="trying out new logger" version=4.2.0 component=demo

Grouping Attributes

Sometimes it maybe useful to have a nested hierarchy of different properties representing an object. A real world example could be a logging middleware which logs an HTTP request.

log.Info("incoming request", "user_id", "ABC123",
slog.Group("http",
    slog.String("method", http.MethodGet),
    slog.Int("status", http.StatusOK),
    slog.Duration("duration", time.Millisecond*250),
    slog.String("method", http.MethodGet),
    slog.String("path", "/api/health")))

time=2023-01-24T17:25:39.239+05:30 level=INFO msg="incoming request" user_id=ABC123 http.method=GET http.status=200 http.duration=250ms http.method=GET http.path=/api/health

We can see that all the HTTP request related metadata is nested under the http group.
JSON Handler

So far, we've seen how to log to logfmt output. However, since slog has a pluggable backend, it means that it can be configured with a different handler and the output format can be "configurable". This is a neat approach since it doesn't involve you change any code to produce a different log output.

log := slog.New(handler.NewJSONHandler(os.Stdout))

Simply updating the handler from TextHandler to JSONHandler is enough:

{"time":"2023-01-24T17:39:22.259975768+05:30","level":"INFO","msg":"trying out new logger"}
{"time":"2023-01-24T17:39:22.260006588+05:30","level":"ERROR","msg":"something went wrong","file":"main.go","err":"file does not exist"}
{"time":"2023-01-24T17:39:22.26001521+05:30","level":"INFO","msg":"incoming request","user_id":"ABC123","http":{"method":"GET","status":200,"duration":250000000,"method":"GET","path":"/api/health"}}

I find JSON to be quite daunting and tedious to read when locally developing applications. However it's a great fit for machine parsing of the logs. logfmt hits the sweet spot, however, with slog one can just use a TextHandler for local environment and JSONHandler for prod. Something like this:

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

APP_ENV=production go run main.go
{"time":"2023-01-24T17:45:22.583057324+05:30","level":"INFO","msg":"Hello world"}

go run main.go                   
time=2023-01-24T17:45:38.406+05:30 level=INFO msg="Hello world"

Overall, I am excited about slog making it's way to stdlib. Gophers
