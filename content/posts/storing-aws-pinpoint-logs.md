+++
date = "2023-07-21T05:24:06+00:00"
description = "A quick guide to stream and process AWS Pinpoint SMS Delivery Logs."
in_search_index = true
og_preview_img = "https://images.unsplash.com/photo-1636955735635-b4c0fd54f360?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wxMTc3M3wwfDF8c2VhcmNofDN8fHZlY3RvcnxlbnwwfHx8fDE2ODk5MTY5OTl8MA&ixlib=rb-4.0.3&q=80&w=2000"
slug = "storing-aws-pinpoint-logs"
title = "Storing AWS Pinpoint Logs"
type = "post"

[taxonomies]
  tags = ["devops", "clickhouse"]

+++


At $dayjob, we use AWS Pinpoint to send out SMS to our customers. We've also written a detailed [blog post](https://zerodha.tech/blog/logging-at-zerodha/) on how we use [Clickhouse](https://clickhouse.com/) + [vector](https://vector.dev/) stack for our logging needs. We additionally wanted to store the delivery logs generated by the Pinpoint service. But like with anything else in AWS, even simpler tasks like these usually tend to piggyback on other counterparts of AWS - in this case, it happens to be AWS Kinesis. All the delivery logs which contain metadata about SMS delivery are streamed to Kinesis.

Our setup involves configuring Pinpoint with Amazon Kinesis Data Firehose stream. Firehose is an ETL service that helps stream events to other persistent stores. Firehose supports multiple such output sinks and in our case we use `HTTP` sink.

This is what the flow looks like:

`Pinpoint -> Kinesis Firehose -> Vector HTTP -> Clickhouse`

---

## Ingesting Data

On the HTTP server side, we used `vector`'s [aws_kinesis_firehose](https://vector.dev/docs/reference/configuration/sources/aws_kinesis_firehose/) source. Compared to just using [http](https://vector.dev/docs/reference/configuration/sources/http_server/) source, here are the differences I found:

- Has first-class support for access_key. AWS Kinesis can be configured to send access_key which comes as the value `X-Amz-Firehose-Access-Key` header in the HTTP request. This means that the request which contains an invalid access key will be rejected at the source itself. However, in the `http` source, I couldn't find a way to drop events at the source level. It is required to use a VRL transformer to check whether `X-Amz-Firehose-Access-Key` is present in the headers and do a value comparison with our key.

- Has native support for `base64` decoding the payload. This one's pretty useful and saved me a lot of VRL transformer rules that I would have otherwise written with the `http` source. So, basically, this is how the server receives the payload:

  ```json
  {
    "requestId": "6a14a06b-6eae-4218-...",
    "timestamp": 1689766125971,
    "records": [
        {
            "data": "eyJld..."
        },
        {
            "data": "eyJldmVudF9..."
        }
    ]
  }
  ```
  
  The value of the payload is a base64 encoded value of the [JSON Object](https://docs.aws.amazon.com/pinpoint/latest/developerguide/event-streams-data-sms.html) of an SMS event. However, the `aws_kinesis_firehose` source is smart enough and automagically decodes this list of records and their values into individual events. This is how the final event looks like when using `aws_kinesis_firehose` source:
  
  ```json
      {
        "message": "{\"event_type\":\"_SMS.SUCCESS\",\"event_timestamp\":1689827914426,\"arrival_timestamp\":1689827917659,\"event_version\":\"3.1\",\"application\":{\"app_id\":\"redacted\",\"sdk\":{}},\"client\":{\"client_id\":\"redacted\"},\"device\":{\"platform\":{}},\"session\":{},\"attributes\":{\"sender_request_id\":\"redacted\",\"destination_phone_number\":\"+91xxx\",\"record_status\":\"DELIVERED\",\"iso_country_code\":\"IN\",\"mcc_mnc\":\"xxx\",\"number_of_message_parts\":\"1\",\"message_id\":\"redacted\",\"message_type\":\"Transactional\",\"origination_phone_number\":\"redactedORG\"},\"metrics\":{\"price_in_millicents_usd\":xx.0},\"awsAccountId\":\"redacted\"}\n",
        "request_id": "6dd45388-xxx",
        "source_arn": "arn:aws:firehose:ap-south-1:redacted:deliverystream/redacted",
        "source_type": "aws_kinesis_firehose",
        "timestamp": "2023-07-20T04:39:38.772Z"
    }
  ```
  
  This makes it straightforward because now we just have to parse the JSON inside the `message` key and do transformations on that object. If it was `http` source, then I'd to loop over the records structure and figure out how to split them as individual events for the rest of the Vector pipeline... which would have been messy to say the least.

Here's the vector config so far:

```toml
[sources.firehose]
# General
type = "aws_kinesis_firehose"
address = "127.0.0.1:9000"
store_access_key = false
access_keys = ["superdupersecret"]

# Use it for debugging
[sinks.console]
type = "firehose"
inputs = ["format_pinpoint_logs"]
encoding.codec = "json"

```

## Formatting the data

Now that we have a pipeline which sends and receives data, we can process the events and transform them into a schema that is more desirable. Since we require the events to be queryable in a Clickhouse DB, this is the schema we have:

```sql
CREATE TABLE default.pinpoint_logs (
    `_timestamp` DateTime('Asia/Kolkata'),
    `app_id` LowCardinality(String),
    `event_type` LowCardinality(String),
    `record_status` LowCardinality(String),
    `origination_phone_number` String,
    `message_id` String,
    `destination_phone_number` String,
    `arrival_timestamp` DateTime('Asia/Kolkata'),
    `event_timestamp` DateTime('Asia/Kolkata'),
    `meta` Nullable(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(_timestamp)
ORDER BY _timestamp
SETTINGS index_granularity = 8192;
```

To achieve the above format, we can use VRL to parse and format our SMS events:

```toml
[transforms.format_pinpoint_logs]
type = "remap" 
inputs = ["firehose"] 
source = '''
  # Decode the JSON message and set ingestion timestamp
  .message = parse_json!(.message)
  .ingestion_timestamp = .timestamp

  # Convert timestamps from Unix to DateTime
  .event_timestamp = from_unix_timestamp!(.message.event_timestamp, unit:"milliseconds")
  .arrival_timestamp = from_unix_timestamp!(.message.arrival_timestamp, unit:"milliseconds")

  # Extract keys to top level and remove from attributes
  .record_status = del(.message.attributes.record_status)
  .origination_phone_number = del(.message.attributes.origination_phone_number)
  .destination_phone_number = del(.message.attributes.destination_phone_number)
  .message_id = del(.message.attributes.message_id)

  # Encode the remaining attributes as JSON string
  .attr = encode_json(.message.attributes)

  # Format Payload for Clickhouse
  . = {
    "_timestamp": .ingestion_timestamp,
    "arrival_timestamp": .arrival_timestamp,
    "event_timestamp": .event_timestamp,
    "app_id": .message.application.app_id,
    "event_type": .message.event_type,
    "record_status": .record_status,
    "message_id": .message_id,
    "origination_phone_number": .origination_phone_number,
    "destination_phone_number": .destination_phone_number,
    "meta": .attr
  }
'''

```

Plugging this, we have a clean JSON object for each SMS event. The only thing now we need to add is an output sink to Clickhouse:

```TOML
[sinks.clickhouse]
type = "clickhouse"
inputs = ["format_pinpoint_logs"]
skip_unknown_fields = true
compression = "gzip"
database = "default"
endpoint = "http://127.0.0.1:8123"
table = "pinpoint_logs"
encoding.timestamp_format = "unix"
batch.max_bytes = 1049000 # 1 MB
batch.timeout_secs = 5
buffer.max_size = 268435488
buffer.type = "disk"
buffer.when_full = "block"
```

Perfect! On running this pipeline with `vector -c config.toml` we can see the consumption the records

Hope this short post was useful if you've to do anything similar!

Fin!
