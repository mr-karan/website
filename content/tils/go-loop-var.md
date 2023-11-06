+++
title = "Golang: The Loop Variable Trap"
date = 2023-09-20
type = "til"
description = "An exploration of a common concurrency issue in Go when using loop variables inside goroutines and how to address it."
in_search_index = true
[taxonomies]
tags = ["Golang", "Concurrency"]
+++

In Go, one of the most popular features is the ability to easily create lightweight concurrent threads using goroutines. While goroutines make concurrent programming simpler, they come with their own set of quirks that can be a source of subtle bugs if not understood well.

## The Issue

When you launch a goroutine inside a loop, and the goroutine function references the loop variable, you might encounter unexpected behavior. Instead of each goroutine using its respective loop iteration value, they might all end up using the last value of the loop variable.

Here's a simple demonstration:

```go
values := []string{"a", "b", "c"}
for _, v := range values {
    go func() {
        fmt.Println(v)
    }()
}
```

You might expect this to print (the order of the goroutines' execution is not guaranteed, but you'll still see 3 different values):

```sh
a
b
c
```

But instead you will see this:

```sh
c
c
c
```

## The Reason

The loop variable `v` is shared among all goroutines. Since the goroutines don't execute immediately and are scheduled to run, by the time they start executing, the loop might have already completed its iterations, leaving `v` with its last value, "c".

Here's a step-by-step of what happens:

1. Loop iteration starts with `v = "a"`.
2. A goroutine is launched which references `v`.
3. Before the goroutine has a chance to execute, the loop moves to the next iteration.
4. `v` now takes the value "b".
5. Another goroutine is launched, also referencing `v`.
6. Again, before this new goroutine has a chance to execute, the loop moves to the next iteration.
7. `v` now takes the value "c".
8. A third goroutine is launched, also referencing `v`.
9. At this point, depending on the scheduler and system, one or more of the goroutines might start executing. But all of them see `v` as "c" since they all reference the same memory location (the address of `v`), which by now has been set to "c" by the loop in the main goroutine.

So, when each of these goroutines tries to read the value of `v`, they all see "c", hence printing "c" three times.

## The Solution

To ensure each goroutine receives the correct value from the loop iteration, pass the loop variable as an argument to the goroutine's function:

```go
values := []string{"a", "b", "c"}
for _, v := range values {
    go func(val string) {
        fmt.Println(val)
    }(v)  // passing the loop variable as an argument
}
```

By passing the value of `v` as an argument to the anonymous function, you effectively make a copy of the value for each iteration of the loop, so each goroutine will see the value of `v` that was present at the time it was launched.

## Conclusion

When working with goroutines inside loops, always be wary of capturing the loop variable directly. Passing it as an argument can help avoid this subtle trap and ensure your concurrent code behaves as intended.
