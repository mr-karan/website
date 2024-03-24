+++
title = "Using slog for logging in Go"
date = 2024-03-18
type = "til"
description = "How I initialise a logger in Go"
in_search_index = true
[taxonomies]
tags = ["Golang"]
+++

## Initialise a base logger


```go
// InitLogger initialies a logger.
func InitLogger(lvl, env, version string) *slog.Logger {
	var logLvl = new(slog.LevelVar)
	if lvl == "debug" {
		logLvl.Set(slog.LevelDebug)
	}
	// Replace internal attributes.
	replace := func(groups []string, a slog.Attr) slog.Attr {
		if a.Key == slog.SourceKey {
			if source, ok := a.Value.Any().(*slog.Source); ok {
				// Remove the function name from the source as it's too noisy.
				source.Function = ""
			}
		}
		return a
	}

	h := slog.NewJSONHandler(
		os.Stderr,
		&slog.HandlerOptions{
			AddSource:   true,
			Level:       logLvl,
			ReplaceAttr: replace,
		},
	).WithAttrs([]slog.Attr{
		slog.String("version", version),
		slog.String("environment", env),
	})
	return slog.New(h)
}
```
