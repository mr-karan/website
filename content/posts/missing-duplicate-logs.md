+++
date = "2023-02-16T08:27:13+00:00"
description = "A paradoxical debugging saga. Learn about inodes, log rotation, and how to make them work in conjunction."
in_search_index = true
og_preview_img = "https://images.unsplash.com/photo-1611517976630-163467322778?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxMTc3M3wwfDF8c2VhcmNofDN8fHB1enpsZXxlbnwwfHx8fDE2NzY1MzYwMTM&ixlib=rb-4.0.3&q=80&w=2000"
slug = "missing-duplicate-logs"
title = "The curious case of missing and duplicate logs"
type = "post"
[taxonomies]
  tags = ["debugging", "devops"]
+++


At work, we use a [Vector](https://vector.dev/) pipeline for processing and shipping logs to [Clickhouse](https://clickhouse.com/). We also self-host our SMTP servers and recently started using [Haraka SMTP](https://github.com/haraka/Haraka). While Haraka is excellent in raw performance and throughput, it needed an external logging plugin for audit and compliance purposes. I wrote [haraka-plugin-outbound-logger](https://github.com/mr-karan/haraka-plugin-outbound-logger) to log basic metadata like timestamps/subject/SMTP response in a JSON file.

The plan was to dump these logs into a file and use Vector's file source for reading them and doing the further transformation. However, things went differently than I had planned. There were mainly two issues propped up due to bad Vector configuration.

### Missing logs

The vector configuration to read the file looked like this:

```toml
[sources.outbound_logger]
type = "file"
include = ["/var/log/haraka/outbound/*.log"]
read_from = "beginning"
# Remove the files after 24 hours. Vector must have permission to delete these files.
remove_after_secs = 86400
fingerprint.strategy = "device_and_inode"

```

Vector has a handy configuration of _automagically_ deleting the file if the file hasn't received any new write in the configured time interval. So `remove_after_secs=86400` specifies if the file hasn't had any new writes since 24h, it can delete it. It made sense to configure because our workload was a shorter process. It was a batch job done once every N days.

When the file didn't receive any new writes after 24h, `vector` deleted the file as expected. However, the plugin continued logging into the _same_ file handler, even for newer batch jobs. As a result, the file didn't receive any new logs and was empty.

I created a minimal POC to reproduce this seemingly strange issue:

```JS
var pino = require('pino');

// Initialise pino js logger and inject in the plugin context.
var opts = {
    name: 'outbound_logger',
    level: 'debug',
    // uses the ISO time format.
    timestamp: pino.stdTimeFunctions.isoTime,
    formatters: {
        level: (label) => {
            return { level: label };
        },
    },
}

pilog = pino(opts, pino.destination(`${__dirname}/app.log`))

pilog.info('this is a first message')
setTimeout(() => pilog.info('this message should get logged'), 10000)
pilog.info('this message will be recorded as well')
```

This snippet logs to `app.log`.

```json
{"level":"info","time":"2023-02-16T06:45:04.031Z","pid":206573,"hostname":"pop-os","name":"outbound_logger","msg":"this is a first message"}
{"level":"info","time":"2023-02-16T06:45:04.031Z","pid":206573,"hostname":"pop-os","name":"outbound_logger","msg":"this message will be recorded as well"}

```

During the 10s time interval, I deleted the file from the disk `rm app.log` to mimic the behaviour of ``remove_after_secs``. I expected the file to get re-created and `this message should get logged` logged by the above script.

However, that **didn't** happen. The script didn't complain about a missing file, either. I was perplexed and did some google-fu and found the following via [Stackoverflow](https://stackoverflow.com/a/19304284/709452):

> The writes actually do not fail.When you delete a file that is open in another program you are deleting a named link to that file's inode. The program that has it open still points to that inode. It will happily keep writing to it, actually writing to disk. Only now you don't have a way to look it at, because you deleted the named reference to it. (If there were other references, e.g. hard links, you would still be able to!).

This is exactly what was happening in production. When `vector` deleted the file (as configured via `remove_after_secs` ), the plugin didn't know about it and kept writing to the same inode. This was a major TIL moment for me.

**Fix**: The fix was simple enough; I removed ``remove_after_secs`` from Vector's config. To address the problem of the file not growing unbounded forever, I created a `logrotate` config:

```ini
/opt/app/logs/app.log {
    daily
    rotate 15
    dateext
    dateformat -%Y-%m-%d.log
    delaycompress
    compress
    notifempty
    missingok
    copytruncate
}
```

Some notes:

* `copytruncate` is useful in this context. It copies the existing file to a new one, which now becomes a stale one. The current (active) file will be truncated to zero bytes. E.g., if `app.log` it is rotated, logrotate will copy the file to a new file `app-2023-02-05.log` and then truncate the existing one to zero bytes.
* `delaycompress` will not compress the logs until the next rotation happens. This is useful if `vector` hasn't finished processing the log and can continue to do that.

### Duplicate Logs

Now after fixing the case of missing logs, I found myself in the opposite problem - now the logs were _duplicated_ on Clickhouse.

My mental state at that moment couldn't be more accurately described than this meme:

![img](/images/missing-duplicate-logs-this-is-fine.jpeg)

To add more context, before developing my plugin for logging email delivery in Haraka, we used another plugin ([acharkizakaria/haraka-plugin-accounting-files](https://github.com/acharkizakaria/haraka-plugin-accounting-files)) to get these logs. This plugin records the metadata to CSV files. Still, there were some issues in properly escaping the subject lines (if the subject had a comma, that was incorrectly parsed); hence, the log file had inconsistent output. To address these issues, I found writing another plugin from scratch that outputs to a fixed JSON schema is better.

As seen above, `vector`'s file source was configured like the following for reading CSV files. The only change here is that `remove_after_secs` is gone after fixing issue #1.

```toml
[sources.outbound_logger]
type = "file"
include = ["/var/log/haraka/outbound/*.log"]
read_from = "beginning"
fingerprint.strategy = "device_and_inode"
```

Vector "[fingerprints](https://vector.dev/docs/reference/configuration/sources/file/#fingerprint)" the file source, as it keeps the checkpoint of how many bytes it has read for each file in its own "disk buffer". This buffer is helpful if Vector crashes so it can restart reading the file from where it last stopped.

There are two strategies for fingerprinting that vector uses:

* The `checksum` strategy uses CRC check on the first N lines of the file.
* The `device_and_inode strategy` uses the disk's actual inode location to identify the file uniquely.

As I was using a different plugin which logged to a CSV file, the checksum strategy did not work in my context. Since vector fingerprints, the first few bytes (usually just enough for a header of a CSV), all the CSV files in that disk would have the same title, and Vector would not read all of them. To work around this, I changed the `fingerprint.starategy = "device_and_inode"` so Vector uniquely identifies all CSV files by their inode path. (In hindsight, I should have just used `checksum` with a higher value of [fingerprint.lines](https://vector.dev/docs/reference/configuration/sources/file/#fingerprint.lines) value.)

The mistake this time was when I switched to a JSON log file, I continued with the ``device_and_inode`` strategy. This isn't a problem if there is no log rotation setup. Since I did configure `logrotate` to fix issue #1, as you would have guessed, `copytruncate` created another log file, and because I was using `device_and_inode` strategy, vector thought this was a "new" file to be watched and processed. So now I had duplicate entries from this new file, which is technically just an older log-rotated file.

**The fix:**

```toml
[sources.outbound_logger.fingerprint]
lines = 14
strategy = "checksum"
ignored_header_bytes = 2048
```

I switched back to the default `checksum` strategy and adjusted the thresholds for lines/header bytes to account for JSON logs. The same is also [documented](https://vector.dev/docs/reference/configuration/sources/file/#file-rotation) very clearly in Vector and it was my RTFM moment.

> This strategy avoids the common pitfalls associated with using device and inode names since inode names can be reused across files. This enables Vector to properly tail files across various rotation strategies.

Phew! I am glad after these fixes; `vector` is durably and reliably processing all the logs and `logrotate` is happily working in conjunction as well. I hope documenting my learnings about these production issues would help someone with the same problems.

Fin!

