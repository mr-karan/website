+++
title = "Logging SMTP connection timings"
date = 2024-02-22
type = "til"
description = "A small python script to log the timings in an SMTP connection"
in_search_index = true
[taxonomies]
tags = ["Python"]
+++


```py
import smtplib
import time

def print_time_taken(start, end, step):
    print(f"{step} took {end - start:.2f} seconds.")

def main():
    smtp_server = "faulty-smtp-host.com"
    smtp_port = 25

    total_start = time.time()

    # Connect to the SMTP server
    connect_start = time.time()
    server = smtplib.SMTP(smtp_server, smtp_port)
    connect_end = time.time()
    print_time_taken(connect_start, connect_end, "Connection")

    # Send EHLO
    ehlo_start = time.time()
    server.ehlo()
    ehlo_end = time.time()
    print_time_taken(ehlo_start, ehlo_end, "EHLO")

    # Send STARTTLS
    starttls_start = time.time()
    server.starttls()
    starttls_end = time.time()
    print_time_taken(starttls_start, starttls_end, "STARTTLS")

    # Re-send EHLO after STARTTLS
    ehlo2_start = time.time()
    server.ehlo()
    ehlo2_end = time.time()
    print_time_taken(ehlo2_start, ehlo2_end, "EHLO after STARTTLS")

    # Quit the session
    quit_start = time.time()
    server.quit()
    quit_end = time.time()
    print_time_taken(quit_start, quit_end, "QUIT")

    total_end = time.time()
    print_time_taken(total_start, total_end, "Total execution")

if __name__ == "__main__":
    main()
```

Produces an output like:

```bash
Connection took 20.09 seconds.
EHLO took 0.01 seconds.
STARTTLS took 0.04 seconds.
EHLO after STARTTLS took 0.01 seconds.
QUIT took 0.01 seconds.
Total execution took 20.15 seconds.
```
