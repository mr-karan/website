+++
title = "Setting Up LiteLLM with AWS Bedrock"
date = 2026-02-11
type = "post"
description = "Practical guide to using AWS Bedrock as an LLM provider via LiteLLM, covering authentication gotchas, parameter conflicts, and per-project cost tracking with Application Inference Profiles."
in_search_index = true
[taxonomies]
tags = ["AWS", "LLM", "Programming"]
+++

I recently set up [LiteLLM](https://github.com/BerriAI/litellm) with AWS Bedrock as the LLM provider. The docs cover the happy path, but there are a few gotchas that cost me some debugging time. This post covers what I learned, from basic setup to per-project cost tracking with Application Inference Profiles.

## Model Format

Bedrock models use the `bedrock/` prefix followed by AWS's model identifiers:

```text
bedrock/anthropic.claude-opus-4-6-v1
bedrock/anthropic.claude-sonnet-4-5-20250929-v1:0
```

Nothing surprising here. LiteLLM uses the prefix to route to the right provider.

## Authentication

This is where the first gotcha lives. Bedrock doesn't use API keys. It authenticates via standard AWS credentials:

- Environment variables: `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- AWS profile: `AWS_PROFILE`
- IAM role (for EC2/ECS/Lambda)

You also need `AWS_REGION_NAME` set to the region where Bedrock is enabled (e.g., `ap-south-1`).

**The gotcha**: don't pass `api_key` to LiteLLM when using Bedrock. If you include an `api_key` parameter in your config, LiteLLM tries to use it instead of the AWS credential chain and auth fails silently. You need to either return `None` for the API key or omit it from the config entirely.

```python
# Wrong - breaks AWS credential chain
llm_config = {"model": "bedrock/anthropic.claude-opus-4-6-v1", "api_key": some_key}

# Correct - let LiteLLM use AWS credentials
llm_config = {"model": "bedrock/anthropic.claude-opus-4-6-v1"}
```

This one took a while to figure out because the error messages don't point you in the right direction.

## The `top_p` and Temperature Conflict

Bedrock's Anthropic models reject requests that include both `temperature` and `top_p`. If your SDK or framework defaults `top_p=1.0`, you need to explicitly clear it:

```python
if model.startswith("bedrock/"):
    llm_config["top_p"] = None
```

Without this, you'll get a validation error from the Bedrock API. The fix is simple, but the error message isn't immediately obvious about what's conflicting.

## Inference Profiles

Bedrock has two types of inference profiles, and the second one is where things get interesting for cost management.

### Cross-Region (System-Defined)

AWS provides these out of the box. They route requests across regions for higher throughput and availability:

```text
global.anthropic.claude-opus-4-6-v1
```

You can list them with:

```bash
aws bedrock list-inference-profiles \
  --type-equals SYSTEM_DEFINED \
  --region ap-south-1
```

### Application Inference Profiles for Cost Tracking

Application Inference Profiles (AIPs) are tagged wrappers around a model. The killer use case is **granular cost attribution** via cost allocation tags. Instead of seeing one blob of "Bedrock spend" in your AWS bill, you can break it down by project, team, or service.

Create one with:

```bash
aws bedrock create-inference-profile \
  --inference-profile-name my-project-opus-4-6 \
  --model-source "copyFrom=arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-opus-4-6-v1:0" \
  --tags key=project,value=my-project \
  --region ap-south-1
```

This gives you an ARN like:

```text
arn:aws:bedrock:ap-south-1:123456789012:application-inference-profile/abcdef123456
```

### Using AIPs with LiteLLM

The standard `bedrock/` route can't parse ARNs. Use the `bedrock/converse/` route instead:

```text
bedrock/converse/arn:aws:bedrock:ap-south-1:123456789012:application-inference-profile/abcdef123456
```

The `bedrock/` prefix still matches for provider detection and the `top_p=None` fix, so no code changes needed on your end.

## Querying Costs via CLI

Once your AIPs are tagged, you can query costs using the Cost Explorer API.

Total Bedrock spend for a month:

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-02-01,End=2026-03-01 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Bedrock"]}}' \
  --region us-east-1
```

Bedrock spend grouped by your cost allocation tag (per-project breakdown):

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-02-01,End=2026-03-01 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Bedrock"]}}' \
  --group-by Type=TAG,Key=project \
  --region us-east-1
```

**Note**: The Cost Explorer API always runs against `us-east-1` regardless of where your resources are deployed.

### Cost Explorer Setup Checklist

A few things to get right before cost data starts flowing:

1. The tag must be an **active cost allocation tag**. Enable it under Billing → Cost Allocation Tags.
2. Use the AIP ARN as the model string in LiteLLM. All invocations through it get tagged automatically.
3. In Cost Explorer, group by tag and select your tag key to see the per-project breakdown.
4. Cost data takes ~24 hours to populate after first usage, so don't panic if it shows up empty initially.

## Dependencies

LiteLLM needs `boto3` to talk to Bedrock:

```text
boto3>=1.28.57
```

Make sure it's installed in your environment, otherwise LiteLLM will fail with an import error when you try to use the `bedrock/` provider.

Fin!
