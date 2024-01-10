+++
title = "One Billion Row Challenge in Go"
date = 2024-01-08
type = "post"
description = "Using Go to efficiently process a massive 12GB file containing 1 billion rows."
in_search_index = true
[taxonomies]
tags= ["Golang"]
+++

Earlier this week, I had stumbled upon [1brc](https://github.com/gunnarmorling/1brc), which presents a fun task: loading a huge text file (1 billion lines) in Java as quickly as possible.

> The One Billion Row Challenge (1BRC) is a fun exploration of how far modern Java can be pushed for aggregating one billion rows from a text file. Utilize all your virtual threads, leverage SIMD, optimize your GC, or employ any other technique to create the fastest implementation for this task!

The challenge is mainly about Java, but I thought to do the same in my preferred language: Go. This post is about how I did several iterations to my Go program to reduce the time and discuss the main techniques used in each iteration to make it faster.

I was able to create a solution which takes **~36s** to read, parse and calculate stats for 1bn lines on my Apple M2 (10 vCPU, 32GB RAM).
There are some _insane_ solutions that people have come up with, be sure to check out [GitHub Discussions](https://github.com/gunnarmorling/1brc/discussions) to go through them! 

## Prerequisites

To generate the text file for these measurements, follow the steps outlined [here](https://github.com/gunnarmorling/1brc?tab=readme-ov-file#prerequisites).

After running the commands, I have a `measurements.txt` on my file system:

Example output after running the commands:

```sh
➜  1brc-go git:(main) du -sh measurements.txt
 13G	measurements.txt
➜  1brc-go git:(main) tail measurements.txt
Mek'ele;13.3
Kampala;50.8
Dikson;-3.7
Dodoma;20.3
San Diego;7.1
Chihuahua;20.3
Ngaoundéré;24.2
Toronto;12.7
Wrocław;12.6
Singapore;14.4
```


## Ultra minimalistic example of reading a file

Let’s take a look at a basic Go code to read and parse the above file. We’ll also calculate stats on the fly.

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

type Measurement struct {
	Station string
	Temp    float64
}

type Stats struct {
	Min, Mean, Max float64
}

func main() {
	// Open the file.
	file, err := os.Open("measurements.txt")
	if err != nil {
		panic(err)
	}
	defer file.Close()

	// Map to hold the temperatures for each station.
	stationTemps := make(map[string][]float64)

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		// Parse each line into a Measurement struct.
		parts := strings.Split(scanner.Text(), ";")
		temp, _ := strconv.ParseFloat(parts[1], 64)
		stationTemps[parts[0]] = append(stationTemps[parts[0]], temp)
	}

	// Calculate min, mean, and max for each station.
	results := make(map[string]Stats)
	for station, temps := range stationTemps {
		min, max, sum := temps[0], temps[0], 0.0
		for _, t := range temps {
			if t < min {
				min = t
			}
			if t > max {
				max = t
			}
			sum += t
		}
		mean := sum / float64(len(temps))
		results[station] = Stats{Min: min, Mean: mean, Max: max}
	}

	// Sort the stations and format the output.
	var stations []string
	for station := range results {
		stations = append(stations, station)
	}
	sort.Strings(stations)

	fmt.Print("{")
	for i, station := range stations {
		r := results[station]
		fmt.Printf("%s=%.1f/%.1f/%.1f", station, r.Min, r.Mean, r.Max)
		if i < len(stations)-1 {
			fmt.Print(", ")
		}
	}
	fmt.Println("}")
}
```

On running the above program, we get the following output:

```sh
{Chihuahua=20.3/20.3/20.3, Dikson=-3.7/-3.7/-3.7, Dodoma=20.3/20.3/20.3, Kampala=50.8/50.8/50.8, Mek'ele=13.3/13.3/13.3, Ngaoundéré=24.2/24.2/24.2, San Diego=7.1/7.1/7.1, Singapore=14.4/14.4/14.4, Toronto=12.7/12.7/12.7, Wrocław=12.6/12.6/12.6}
```

This approach works well for small, simple files. However, there are certain restrictions:

- It reads the file line by line using a scanner. Reading and processing a billion rows is time-consuming.
- Each operation, even if small, adds up when repeated a billion times. This includes string splitting, type conversion, error checking, and appending to a slice.
- Additionally, we need to consider the potential of hitting the max Disk IOPS limit if we perform too many file operations per second.

Before we proceed to optimize this further, let's establish a baseline performance of _100 million_ lines first:

```go
$ wc -l measurements.txt
  100000000 measurements.txt
$ time go run main.go
  go run main.go  18.44s user 0.83s system 100% cpu 19.135 total
```

Baseline: It takes approximately 19s to read and calculate stats from 100 mn lines.

There’s a lot of room to optimize it further, let's go through them one by one.

## Iteration 1: Producer-Consumer Pattern

The concept involves reading multiple lines simultaneously in the producer Goroutine and then dispatching these batches to worker Goroutines. We can establish a worker pool to implement a producer-consumer pattern. Producers read lines from the file and send them to a channel. Consumers retrieve lines from the channel, parse the data, and calculate the minimum, mean, and maximum temperatures for each station.

```go
func main() {
	numWorkers := runtime.NumCPU()
	runtime.GOMAXPROCS(numWorkers)

	linesChan := make(chan string, 1000000)
	resultsChan := make(chan map[string]Stats, numWorkers)

	// Start worker goroutines
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go worker(linesChan, resultsChan, &wg)
	}

	// Read the file and send lines to the workers
	go func() {
		file, err := os.Open(measurementsFile)
		if err != nil {
			panic(err)
		}
		defer file.Close()

		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			linesChan <- scanner.Text()
		}
		close(linesChan)
	}()

	// Collect results from workers
	wg.Wait()
	close(resultsChan)

	// Aggregate results
	finalResults := make(map[string]Stats)
	for workerResult := range resultsChan {
		for station, stats := range workerResult {
			finalStats := finalResults[station]
			finalStats.Min = min(finalStats.Min, stats.Min)
			finalStats.Max = max(finalStats.Max, stats.Max)
			finalStats.Mean = (finalStats.Mean*float64(finalStats.Count) + stats.Mean*float64(stats.Count)) / float64(finalStats.Count+stats.Count)
			finalStats.Count += stats.Count
			finalResults[station] = finalStats
		}
	}

	// Print results
	printStats(finalResults)
}

func worker(linesChan <-chan string, resultsChan chan<- map[string]Stats, wg *sync.WaitGroup) {
	defer wg.Done()

	stationStats := make(map[string]Stats)
	for line := range linesChan {
		parts := strings.Split(line, ";")
		temp, err := strconv.ParseFloat(parts[1], 64)
		if err != nil {
			continue
		}

		stats := stationStats[parts[0]]
		stats.Count++
		stats.Min = min(stats.Min, temp)
		stats.Max = max(stats.Max, temp)
		stats.Mean += (temp - stats.Mean) / float64(stats.Count)
		stationStats[parts[0]] = stats
	}

	resultsChan <- stationStats
}

func min(a, b float64) float64 {
	if a == 0 || a > b {
		return b
	}
	return a
}

func max(a, b float64) float64 {
	if a < b {
		return b
	}
	return a
}

func printStats(statsMap map[string]Stats) {
	var stations []string
	for station := range statsMap {
		stations = append(stations, station)
	}
	sort.Strings(stations)

	fmt.Print("{")
	for i, station := range stations {
		stats := statsMap[station]
		fmt.Printf("%s=%.1f/%.1f/%.1f", station, stats.Min, stats.Mean, stats.Max)
		if i < len(stations)-1 {
			fmt.Print(", ")
		}
	}
	fmt.Println("}")
}
```

### Results

The concurrent version, unexpectedly, resulted in almost a 3x decrease in performance.

```go
go run main.go  84.15s user 101.34s system 342% cpu 54.225 total
```

Where did we go wrong? This is a classic case where the overhead of concurrency mechanisms outweighs their benefits. In our current implementation, each line is sent to the channel individually, which is likely less efficient than batching lines for processing. This means that for a file with a large number of lines, there will be an equally large number of channel send operations. Each channel operation involves locking and unlocking, which can be costly, especially in a high-frequency context.

## Iteration 2: Batch processing of lines

In this version we are Batching the lines before sending to the worker which will significantly reduce the overhead of channel communication.

1. **Batch Processing**: Each batch contains **`batchSize`** lines. This reduces the frequency of channel operations (both sending and receiving), as well as the overhead associated with these operations.

2. **Efficient Worker Utilization**: With batch processing, each worker goroutine spends more time processing data and less time interacting with channels. This reduces the overhead of context switching and synchronization, making the processing more efficient.

```go
const (
	batchSize        = 1000000 // Number of lines per batch
)

// ...
		scanner := bufio.NewScanner(file)
		var batch []string
		for scanner.Scan() {
			batch = append(batch, scanner.Text())
			if len(batch) >= batchSize {
				batchesChan <- batch
				batch = nil // Start a new batch
			}
		}
		// Send any remaining lines in the last batch
		if len(batch) > 0 {
			batchesChan <- batch
		}
		close(batchesChan)

// ...
func worker(batchesChan <-chan []string, resultsChan chan<- map[string]Stats, wg *sync.WaitGroup) {
	defer wg.Done()

	stationStats := make(map[string]Stats)
	for batch := range batchesChan {
		for _, line := range batch {
            // Process the line ...
        }
	}

	resultsChan <- stationStats
}
// ...
```

### Results

The improvement from iteration 2 to iteration 3 is quite remarkable, thanks to efficiently batching the lines together and reducing the number of channel ops.

```bash
go run main.go  30.02s user 0.67s system 476% cpu 6.442 total
```

So far, we've reduced the time to about 6.5s which is a great start and improvement of our baseline version of 19s. However, we're making quite a few extra memory allocations and the focus of next iteration should be to reduce that.

## Iteration 3: Reducing memory allocations

- A batch slice is pre-allocated with a capacity of **`batchSize`** and reused for each batch of lines.
- After sending a batch to the channel, the slice is reset to zero length (`batch = batch[:0]`), but the underlying array is retained and reused.

```go
// Read the file and send batches of lines to the workers
	go func() {
		file, err := os.Open(measurementsFile)
		if err != nil {
			panic(err)
		}
		defer file.Close()

		scanner := bufio.NewScanner(file)
		batch := make([]string, 0, batchSize) // Pre-allocate with capacity

		for scanner.Scan() {
			line := scanner.Text()

			// Reuse the batch slice by appending to it until it reaches the batch size
			batch = append(batch, line)

			if len(batch) >= batchSize {
				batchesChan <- batch
				batch = batch[:0] // Reset the slice without allocating new memory
			}
		}
		// Send any remaining lines in the last batch
		if len(batch) > 0 {
			batchesChan <- batch
		}
		close(batchesChan)
	}()
```

### Results

Down to 5.3s!

```bash
go run main.go  25.43s user 0.53s system 485% cpu 5.346 total
```

## Iteration 3 (cont): Further reducing memory allocations

- Avoiding `strings.Split`: Instead of using `strings.Split`, which allocates a new slice for each line, we can use  `strings.Index` to find the delimiter and manually slice the string. `strings.Split` typically creates a new slice for each split part, leading to more memory usage and subsequent GC overhead.

```go
for batch := range batchesChan {
		for _, line := range batch {
			delimiterIndex := strings.Index(line, ";")
			if delimiterIndex == -1 {
				continue // Delimiter not found, skip this line
			}

			station := line[:delimiterIndex]

			tempStr := line[delimiterIndex+1:]
			temp, err := strconv.ParseFloat(tempStr, 64)
			if err != nil {
				continue // Invalid temperature value, skip this line
			}

			stats := stationStats[station]
			stats.Count++
			stats.Min = min(stats.Min, temp)
			stats.Max = max(stats.Max, temp)
			stats.Mean += (temp - stats.Mean) / float64(stats.Count)
			stationStats[station] = stats
		}
	}
```

### Results

The time has further decreased from 5.3s to 4.8s with these changes.

```go
go run main.go  15.69s user 0.44s system 332% cpu 4.853 total
```

## Iteration 4: Read file in chunks

In this version, the file is read in chunks, and each chunk is processed to ensure it contains complete lines. The `processChunk` function is used to separate valid data from leftover data in each chunk. Chunk size can be controlled with command line args as well.

```go
func main() {
	// ....
	const chunkSize = 256 * 1024 // 256 KB
	buf := make([]byte, chunkSize)
	leftover := make([]byte, 0, chunkSize)

	go func() {
		for {
			bytesRead, err := file.Read(buf)
			if bytesRead > 0 {
				// Copy the chunk to a new slice, because the
				// buffer will be reused in the next iteration.
				chunk := make([]byte, bytesRead)
				copy(chunk, buf[:bytesRead])
				// Process the chunk. The returned leftover will be processed in the next iteration.
				validChunk, newLeftover := processChunk(chunk, leftover)
				leftover = newLeftover
				// Send the valid chunk to the processing goroutine.
				if len(validChunk) > 0 {
					wg.Add(1)
					go processChunkData(validChunk, resultsChan, &wg)
				}
			}
			if err != nil {
				break
			}
		}
		wg.Wait()
		close(resultsChan)
	}()
	// ...
}


func processChunk(chunk, leftover []byte) (validChunk, newLeftover []byte) {
	firstNewline := -1
	lastNewline := -1
	// Find the first and last newline in the chunk.
	for i, b := range chunk {
		if b == '\n' {
			if firstNewline == -1 {
				firstNewline = i
			}
			lastNewline = i
		}
	}
	if firstNewline != -1 {
		validChunk = append(leftover, chunk[:lastNewline+1]...)
		newLeftover = make([]byte, len(chunk[lastNewline+1:]))
		copy(newLeftover, chunk[lastNewline+1:])
	} else {
		newLeftover = append(leftover, chunk...)
	}
	return validChunk, newLeftover
}

func processChunkData(chunk []byte, resultsChan chan<- map[string]Stats, wg *sync.WaitGroup) {
	defer wg.Done()

	stationStats := make(map[string]Stats)
	scanner := bufio.NewScanner(strings.NewReader(string(chunk)))

	for scanner.Scan() {
		line := scanner.Text()

		// Find the index of the delimiter
		delimiterIndex := strings.Index(line, ";")
		if delimiterIndex == -1 {
			continue // Delimiter not found, skip this line
		}

		// Extract the station name and temperature string
		station := line[:delimiterIndex]
		tempStr := line[delimiterIndex+1:]

		// Convert the temperature string to a float
		temp, err := strconv.ParseFloat(tempStr, 64)
		if err != nil {
			continue // Invalid temperature value, skip this line
		}

		// Update the statistics for the station
		stats, exists := stationStats[station]
		if !exists {
			stats = Stats{Min: temp, Max: temp}
		}
		stats.Count++
		stats.Min = min(stats.Min, temp)
		stats.Max = max(stats.Max, temp)
		stats.Mean += (temp - stats.Mean) / float64(stats.Count)
		stationStats[station] = stats
	}

	// Send the computed stats to resultsChan
	resultsChan <- stationStats
}
```

In addition to this, I moved the `aggregateStats` to a separate Goroutine as well:

```go
	aggWg.Add(1)
	finalResults := make(map[string]Stats)

	// Start a separate goroutine for aggregation
	go func() {
		defer aggWg.Done()
		for workerResult := range resultsChan {
			for station, stats := range workerResult {
				finalStats, exists := finalResults[station]
				if !exists {
					finalResults[station] = stats
					continue
				}
				finalStats.Min = min(finalStats.Min, stats.Min)
				finalStats.Max = max(finalStats.Max, stats.Max)
				totalCount := finalStats.Count + stats.Count
				finalStats.Mean = (finalStats.Mean*float64(finalStats.Count) + stats.Mean*float64(stats.Count)) / float64(totalCount)
				finalStats.Count = totalCount
				finalResults[station] = finalStats
			}
		}
	}()
```

### Results

We're down from 4.8s to just 2.1s to read/parse/process 100mn lines! 

```sh
./bin/1brc.bin --file=input.txt --chunksize=1048576  17.58s user 0.77s system 837% cpu 2.190 total
```

## Summary

1. **Basic File Reading and Parsing (Baseline)**: 
   - **Time**: 19s (baseline).
   - **Key Change**: Sequentially reading and processing each line.
   - **Speedup**: N/A (baseline).

2. **Producer-Consumer Pattern**:
   - **Time**: 54.225s.
   - **Key Change**: Implemented concurrent line processing with producer-consumer pattern.
   - **Speedup**: -185% (slower than baseline).

3. **Batch Processing of Lines**:
   - **Time**: 6.442s.
   - **Key Change**: Batched lines before processing, reducing channel communication.
   - **Speedup**: +66% (compared to baseline).

4. **Reducing Memory Allocations - Iteration 1**:
   - **Time**: 5.346s.
   - **Key Change**: Reused batch slices and reduced memory allocations.
   - **Speedup**: +72% (compared to baseline).

5. **Reducing Memory Allocations - Iteration 2 (Avoiding `strings.Split`)**:
   - **Time**: 4.853s.
   - **Key Change**: Replaced `strings.Split` with manual slicing for efficiency.
   - **Speedup**: +75% (compared to baseline).

6. **Read File in Chunks**:
   - **Time**: 2.190s.
   - **Key Change**: Processed file in chunks and optimized aggregation.
   - **Speedup**: +87% (compared to baseline).


## Final Run

I'm quite satisfied with the final version for now. We can now proceed to test it with 1 billion lines. However it's evidently CPU-bound, as we spawn N workers for N CPUs.

I experimented with different chunk sizes, and here are the results from each run:

| Chunk Size | Time    |
| ---------- | ------- |
| 512.00 KB  | 23.756s |
| 1.00 MB    | 21.798s |
| 32.00 MB   | 19.501s |
| 16.00 MB   | 20.693s |

Tweaking the chunk size doesn't significantly impact performance, as processing larger chunks takes longer.

TL;DR: On an average and with multiple runs it takes approx **20s** with the final iteration for 1bn lines.

## Potential Improvements

This project was not only fun but also a great opportunity to revisit and refine many Go concepts. There are several ideas to contemplate for further improving this version's timings:

- I haven't yet considered using `mmap`, but I believe it could substantially speed things up.
- To delve even deeper, custom line parsing functions, especially for converting `string` to `float64`, could offer improvements.
- Employing custom hashing functions (perhaps FnV) might aid in faster map lookups.

Fin!
