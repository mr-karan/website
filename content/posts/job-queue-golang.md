+++
title = "Designing a simple Job Queue in Golang"
date = 2020-12-01T08:10:55+05:30
type = "post"
description = "This is a tutorial for understanding how to design a Job Queue pattern using Golang"
in_search_index = true
[taxonomies]
tags = ["Golang"]
+++

In this post we'll see how to create a simple job queue in Golang. There are tonnes of libraries and posts out there doing overly complicated stuff, however if your need is pretty minimal or you want to understand the concepts from ground up, this post aims to do just that and nothing more.

We'll be using concepts like [WaitGroup](https://golang.org/pkg/sync/#WaitGroup), [Channels](https://golang.org/doc/effective_go.html#concurrency) and [Contexts](https://golang.org/pkg/context/) to build our own Job Queuing mechanism. It primarily involves 2 components:

- **Queue**: A queue which has a list of items waiting to be processed.

- **Worker**: A *worker* constantly listening to that queue and *processing* the events as desired.

With these 2 main ideas behind us, let us create our sample structure:

```go
package dispatch

type Dispatcher interface {
	// Push takes an Event and pushes to a queue.
	Push(Event) error
	// Run spawns the workers and waits indefinitely for
	// the events to be processed.
	Run()
}

// EventDispatcher represents the datastructure for an
// EventDispatcher instance. This struct satisfies the
// Dispatcher interface.
type EventDispatcher struct {
	Opts     Options
	Queue    chan models.Notification
	Finished bool
}

// Options represent options for EventDispatcher.
type Options struct {
	MaxWorkers int // Number of workers to spawn.
	MaxQueueSize int // Maximum length for the queue to hold events.
}

// NewEventDispatcher initialises a new event dispatcher.
func NewEventDispatcher(opts Options) (Dispatcher) {
	return EventDispatcher{
		Opts: opts,
		Queue: make(chan Event, opts.MaxQueueSize),
		Finished: false,
	}
}
```

### Pushing to Queue

Now that we have our basic structure ready, let's write a function to push events to queue.

A queue is simply a channel. We have created a new queue of size `MaxQueueSize` while initialising the `EventDispatcher`. 

```
Queue: make(chan Event, opts.MaxQueueSize)
```

To push events into it, we'll simply do: `d.Queue <- event`. This adds a new item (`event`) of type `Event` to our queue.

```go
// Push adds a new event payload to the queue.
func (d *EventDispatcher Push(event Event) error {
	if d.Finished {
		return errors.New(`queue is closed`)
	}
	d.Queue <- event
	return nil
}
```

### Listening to Queue

So the client is calling `Push()` on our `EventDispatcher` and events are being pushed in the channel. But there's no one reading from this channel so far. Let's fix that by spawning workers, who will listen on the channel *indefinitely* and process the events:

```go
for {
    select {
        case event <- d.Queue:
        event.Process()
    }
}
```

In the above snippet, we are simply looping indefinitely to scan through all items in the queue. `event <- d.Queue` is basically fetching the item from the channel and assigning a value to it. 

`event.Process()` is a dummy function but it basically indicates that whatever processing that needs to be done should be handled here.

Right now, you'll be wondering two things:

- If this is an infinite loop, how do we guarantee it runs forever?
- How do I spawn more workers if I need concurrency?

To address these problems, let's add in WaitGroups and GoRoutines to our mix. 

WaitGroups will help us keep a count of workers which have been spawned and until each one of them finishes processing, wait groups will keep blocking indefinitely using `wg.Wait()`. 

And to bring in more workers, we'll simply spawn them with GoRoutines:

```go
go func() {
	for {
	  select {
	    case event <- d.Queue:
		event.Process()
	  }
	}
}()
```

Now, spawning `n` Goroutines is just a matter of a simple for loop over this:

```go
for i:=0; i<d.Opts.MaxWorkers; i++{
	wg.Add(1) // Add a wait group for each worker
	go func() {
		for {
		select {
			case event <- d.Queue:
			event.Process()
		}
		}
	}()
}
```

Perfect! But hang on! We have missed a critical thing. How do we handle cancellations? For eg, when your program shuts down, we should clean up all the Goroutines spawned and process the remaining messages in queue. For that, we need to listen to a `Cancellation` channel. The only purpose of this channel is to listen for SIGINT or SIGTERM signals and whenever either of them is received, we should flush our events.

Here's how the client would initialise a context:

```go
// Create a channel to relay `SIGINT` and `SIGTERM` signals.
closeChan := make(chan os.Signal, 1)
signal.Notify(closeChan, os.Interrupt, syscall.SIGTERM)
ctx, cancel := context.WithCancel(context.Background())
```

And in the main thread, the client would block on `closeChan` channel like:

```go
// Listen on close channel indefinitely until a
// `SIGINT` or `SIGTERM` is received.
<-closeChan
// Cancel the context to gracefully shutdown.
cancel()
```

When `cancel()` is called, it does something special. It passes a value to `ctx.Done()` channel. We can listen to this channel in the `.Run()` function and flush pending events accordingly:

```go
case <- ctx.Done():
	// Ensure no new messages are added.
	d.Finished = true
	// Flush all events.
	e.Flush()
	// This Goroutine has finished processing.
	wg.Done()
```

---

Stitching all pieces together, we finally have: 

```go
package dispatch

type Dispatcher interface {
	// Push takes an Event and pushes to a queue.
	Push(Event) error
	// Run spawns the workers and waits indefinitely for
	// the events to be processed.
	Run()
}

// EventDispatcher represents the datastructure for an
// EventDispatcher instance. This struct satisfies the
// Dispatcher interface.
type EventDispatcher struct {
	Opts     Options
	Queue    chan models.Notification
	Finished bool
}

// Options represent options for EventDispatcher.
type Options struct {
	MaxWorkers int // Number of workers to spawn.
	MaxQueueSize int // Maximum length for the queue to hold events.
}

// NewEventDispatcher initialises a new event dispatcher.
func NewEventDispatcher(opts Options) (Dispatcher) {
	return EventDispatcher{
		Opts: opts,
		Queue: make(chan Event, opts.MaxQueueSize),
		Finished: false,
	}
}

// Push adds a new event payload to the queue.
func (d *EventDispatcher Push(event Event) error {
	if d.Finished {
		return errors.New(`queue is closed`)
	}
	d.Queue <- event
	return nil
}

// Run spawns workers and listens to the queue
// It's a blocking function and waits for a cancellation
// invocation from the Client.
func (d *EventDispatcher Run(ctx context.Context) {
	wg := sync.WaitGroup{}
	for i := 0; i < d.Opts.MaxWorkers; i++ {
		wg.Add(1) // Add a wait group for each worker
		// Spawn a worker
		go func() {
			for {
				select {
				case <-ctx.Done():
					// Ensure no new messages are added.
					d.Finished = true
					// Flush all events
					e.Flush()
					wg.Done()
					return
				case e <- d.Queue:
					e.Process()
				}
			}
		}()
	}
	wg.Wait()
}

// Push adds a new event payload to the queue.
func (d *EventDispatcher Push(event Event) error {
	if d.Finished {
		return errors.New(`queue is closed`)
	}
	d.Queue <- event
	return nil
}
```

This post doesn't cover how to flush or process the events as these are implementation specific details.
This is a pretty barebones structure and you can modify the code according to your usecase.

Fin!
