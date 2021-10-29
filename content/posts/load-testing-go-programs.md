+++
title = "Load testing with K6"
date = 2021-10-29T00:00:00+05:30
type = "post"
description = "A short post on how to use K6 for performing different kinds of load tests on a Go Application"
in_search_index = true
[taxonomies]
tags = ["Golang"]
[extra]
og_preview_img = "/images/k6.png"
+++

This week I was occupied with optimising a Golang program I'd written at work. I wanted a way to reproduce the issue under heavy load on my development environment and Load Tests are a good way to do that.

The service in question is a RESTful API so it's relatively easy to use any HTTP load test tools. The endpoint had an input parameter `uuid` which accepted a valid `UUIDv4` as the input. To my surprise, this was not so straightforward with [hey](https://github.com/rakyll/hey) (which is my tool of choice for simple tests) and [ab](https://github.com/CloudFundoo/ApacheBench-ab). While it was possible to write an external script to do that, I thought to look around at some "scriptable" alternatives. I found [wrk](https://github.com/wg/wrk) which allowed me to write custom Lua modules. Now, I didn't want to lose my focus from the main task which was load testing my service to write Lua, so I didn't use `wrk` but it's still a pretty decent option (and _very very_ fast, at that).

## Hello k6!

![image](/images/k6.png)

Some more Google-fu resulted in me finding [k6](https://k6.io/). I'd never heard of this but after exploring the [GitHub repo](https://github.com/grafana/k6) and the docs it looks like a pretty active project.

So, `k6` basically allows you to write scriptable tests which allow you to test a variety of [scenarios](https://k6.io/docs/using-k6/scenarios/). The scripts are written in Javascript and treated as ES6 Modules for extensibility. `k6` has a concept of [Virtual Users](https://k6.io/docs/cloud/cloud-faq/general-questions/#what-are-vus-virtual-users) to mimic a real-world user. Each VU runs the "script" in an isolated self-contained JS runtime using [Goja](https://github.com/dop251/goja). Now obviously at this point, if speed is your utmost concern to generate very heavy load tests, I guess `wrk` is your only real choice as invoking a JS runtime inside Go won't be super fast. But for most use-cases and people, like my case, this will just be fine.

## Basic Usage

Anyway, I quickly grokked the docs and copy-pasted some examples and modified them to what I needed. I was able to run a basic load test running very quickly and admired the simplicity here. It generated some p90, p95 etc stats which were helpful to look at. Here's a basic example of how the script looks:

```js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.0.0/index.js";

export const errorRate = new Rate('errors');

export default function () {
  const url = 'https://httpbin.org/post';
  const params = {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  };

  const data = {
    custname: "hello",
    comments: uuidv4(),
  };
  check(http.post(url,data, params), {
    'status is 200': (r) => r.status == 200,
  }) || errorRate.add(1);

  sleep(0.5);
}
```

**To run it:**

```bash
k6 run -d 10s -u 10 httpbin_load.js
```

(Here `-d` is for the duration to run the test and `-u` is to specify `Virtual User`)

**Explanation:**

- It's an `HTTP POST` request with some form data to [https://httpbin.org/post](https://httpbin.org/post)
- We use the [uuid](https://k6.io/docs/javascript-api/jslib/utils/uuidv4/) function because the JS stdlib is _great_ at providing basic helper methods (/s)
- We define a check for HTTP status code as 200. Later we'll see how to add more real-world checks under heavy load.
- We have a [sleep](https://k6.io/docs/javascript-api/k6/sleep-t/) function to pause a little bit before each iteration. This is pretty important as leaving `sleep` is akin to a user pressing F5 on a browser non-stop and you'd probably not want your load tests to be that aggressive. Read [docs](https://k6.io/docs/using-k6/test-life-cycle/#the-default-function-life-cycle) for more info.

**Output:**

```
❯ k6 run -d 30s -u 10 test.js                   

          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: test.js
     output: -

  scenarios: (100.00%) 1 scenario, 10 max VUs, 1m0s max duration (incl. graceful stop):
           * default: 10 looping VUs for 30s (gracefulStop: 30s)


running (0m30.6s), 00/10 VUs, 387 complete and 0 interrupted iterations
default ✓ [======================================] 10 VUs  30s

     ✓ status is 200

     checks.........................: 100.00% ✓ 387       ✗ 0   
     data_received..................: 318 kB  10 kB/s
     data_sent......................: 78 kB   2.5 kB/s
     http_req_blocked...............: avg=28.65ms  min=210ns    med=857ns    max=1.1s     p(90)=1.49µs   p(95)=1.68µs  
     http_req_connecting............: avg=7.77ms   min=0s       med=0s       max=301.24ms p(90)=0s       p(95)=0s      
     http_req_duration..............: avg=254.05ms min=215.63ms med=231.15ms max=826.99ms p(90)=317.33ms p(95)=325.1ms 
       { expected_response:true }...: avg=254.05ms min=215.63ms med=231.15ms max=826.99ms p(90)=317.33ms p(95)=325.1ms 
     http_req_failed................: 0.00%   ✓ 0         ✗ 387 
     http_req_receiving.............: avg=177.35µs min=39.43µs  med=170.18µs max=604.22µs p(90)=259.75µs p(95)=285.73µs
     http_req_sending...............: avg=268.41µs min=48.62µs  med=216.61µs max=7.95ms   p(90)=334.94µs p(95)=448.21µs
     http_req_tls_handshaking.......: avg=15.87ms  min=0s       med=0s       max=615.25ms p(90)=0s       p(95)=0s      
     http_req_waiting...............: avg=253.61ms min=215.34ms med=230.77ms max=826.57ms p(90)=316.98ms p(95)=324.69ms
     http_reqs......................: 387     12.666038/s
     iteration_duration.............: avg=784ms    min=717ms    med=732.43ms max=1.92s    p(90)=820.35ms p(95)=926.87ms
     iterations.....................: 387     12.666038/s
     vus............................: 10      min=10      max=10
     vus_max........................: 10      min=10      max=10
```

**Things to look for:**

From the above output, I think these 2 metrics are the most important to look at:

```
     http_req_duration..............: avg=254.05ms min=215.63ms med=231.15ms max=826.99ms p(90)=317.33ms p(95)=325.1ms 
     http_reqs......................: 387     12.666038/s
```

We see the total requests sent in 30s were `387` and the `p95` response time is `325.1ms`.

## Testing some real-world scenarios

This was a really simple example but we can add some more scenarios to mimic real-world checks. Let's tweak the script to

- Go from 1 to 10 users in 10s.
- Stay at 10 users for 5s.
- Ramp down to 1 user for the next 15s.
- Have a threshold of not exceeding 500ms as p95.
- Have a threshold for the count of non `200 OK` responses.

The above script now becomes:

```js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.0.0/index.js";

export const errorRate = new Rate('non_200_requests');

export let options = {
    stages: [
        // Ramp-up from 1 to 10 VUs in 10s.
        { duration: "10s", target: 10 },

        // Stay at rest on 10 VUs for 5s.
        { duration: "5s", target: 10 },

        // Linearly ramp down from 10 to 0 VUs over the last 15s.
        { duration: "15s", target: 0 }
    ],
    thresholds: {
        // We want the 95th percentile of all HTTP request durations to be less than 500ms
        "http_req_duration": ["p(95)<500"],
        // Thresholds based on the custom metric `non_200_requests`.
        "non_200_requests": [
            // Global failure rate should be less than 1%.
            "rate<0.01",
            // Abort the test early if it climbs over 5%.
            { threshold: "rate<=0.05", abortOnFail: true },
        ],
    },
};

export default function () {
  const url = 'https://httpbin.org/post';
  const params = {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  };

  const data = {
    custname: "hello",
    comments: uuidv4(),
  };
  check(http.post(url,data, params), {
    'status is 200': (r) => r.status == 200,
  }) || errorRate.add(1);

  sleep(Math.random() * 1 + 1); // Random sleep between 1s and 2s.
}
```

Run with `k6 run test.js`:

```
2.21.0 on ☁️  (ap-south-1) took 24s 
❯ k6 run test.js

          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: test.js
     output: -

  scenarios: (100.00%) 1 scenario, 10 max VUs, 1m0s max duration (incl. graceful stop):
           * default: Up to 10 looping VUs for 30s over 3 stages (gracefulRampDown: 30s, gracefulStop: 30s)


running (0m30.3s), 00/10 VUs, 105 complete and 0 interrupted iterations
default ✓ [======================================] 00/10 VUs  30s

     ✓ status is 200

     checks.........................: 100.00% ✓ 105      ✗ 0   
     data_received..................: 126 kB  4.2 kB/s
     data_sent......................: 25 kB   841 B/s
     http_req_blocked...............: avg=73.69ms  min=292ns    med=761ns    max=1.02s    p(90)=1.54µs   p(95)=688.76ms
     http_req_connecting............: avg=21.67ms  min=0s       med=0s       max=245.46ms p(90)=0s       p(95)=223.77ms
   ✓ http_req_duration..............: avg=252.72ms min=215.88ms med=230.31ms max=560.17ms p(90)=299.12ms p(95)=406.94ms
       { expected_response:true }...: avg=252.72ms min=215.88ms med=230.31ms max=560.17ms p(90)=299.12ms p(95)=406.94ms
     http_req_failed................: 0.00%   ✓ 0        ✗ 105 
     http_req_receiving.............: avg=177.85µs min=103.82µs med=163.76µs max=366.5µs  p(90)=235.86µs p(95)=266.39µs
     http_req_sending...............: avg=258.17µs min=96.92µs  med=215.88µs max=958.67µs p(90)=410.05µs p(95)=487.18µs
     http_req_tls_handshaking.......: avg=50.22ms  min=0s       med=0s       max=614.14ms p(90)=0s       p(95)=460.3ms 
     http_req_waiting...............: avg=252.29ms min=215.17ms med=229.69ms max=559.86ms p(90)=298.42ms p(95)=406.52ms
     http_reqs......................: 105     3.471037/s
     iteration_duration.............: avg=1.84s    min=1.22s    med=1.85s    max=3.02s    p(90)=2.22s    p(95)=2.46s   
     iterations.....................: 105     3.471037/s
     vus............................: 1       min=1      max=10
     vus_max........................: 10      min=10     max=10
```

We can see that all the checks passed without breaching any thresholds we'd set.

**Some important points**:

- In my local environment, I stress tested my service with 10k VUs which is quite a high number for the service but it was good to see it hold under extreme conditions as well. An important thing to note if you are spawning many VUs is that `ulimit` number should be high. This is [described in their docs](https://k6.io/docs/misc/fine-tuning-os/) as well.

- To debug the HTTP response you can run with `--http-debug="full"` flag and get the verbose output for debugging.

## Summary

I've barely scratched the surface of what this tool does. You can export metrics to various data sources, add a lot more checks on the response code, use it with GRPC or WebSockets as well. 

Overall pretty happy with this tool and I am going to use more of it for future projects.

### References

- [https://k6.io/blog/comparing-best-open-source-load-testing-tools/](https://k6.io/blog/comparing-best-open-source-load-testing-tools/)
- [https://k6.io/our-beliefs/#simple-testing-is-better-than-no-testing](https://k6.io/our-beliefs/#simple-testing-is-better-than-no-testing)
- [https://k6.io/docs/](https://k6.io/docs/)
- [https://github.com/grafana/k6](https://github.com/grafana/k6)

Fin
