+++
title = "Explicit Account Routing in OpenCode with CLIProxyAPI"
date = 2026-10-21
type = "post"
description = "Using CLIProxyAPI and a small OpenCode plugin to keep personal and work LLM accounts strictly separated."
in_search_index = true
[taxonomies]
tags = ["AI", "LLM", "Programming"]
+++

I juggle between personal and work accounts for both Claude and Codex, and I wanted all of them available in [OpenCode](https://opencode.ai/v2/docs/).

Most people set up local LLM proxies to pool their accounts into one bucket and auto-failover when a rate limit hits. I wanted the exact opposite. If I'm working on a company repo and hit a usage cap, the request should just fail. It should never quietly fall back to my personal account in the background.

I use [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) to handle the OAuth logins, token refreshes, and upstream requests. It supports account-specific prefixes, so I can give each login a clear label like `claude-work` or `codex-personal`.

## Why a plugin?

Pointing OpenCode at the proxy is easy enough, but OpenCode doesn't query `/v1/models` to discover what an endpoint actually serves. It only shows the models you hardcode in its config file. Maintaining that list by hand across multiple accounts gets old fast.

To fix that, I wrote a small local OpenCode plugin (`local.cliproxy`) in TypeScript using `@opencode/plugin`.

In my OpenCode config, I pass the plugin the list of account prefixes I want exposed and whether each one speaks Anthropic or OpenAI under the hood:

```json
{
  "accounts": [
    { "id": "claude-work", "provider": "anthropic" },
    { "id": "claude-personal", "provider": "anthropic" },
    { "id": "codex-work", "provider": "openai" },
    { "id": "codex-personal", "provider": "openai" }
  ]
}
```

### How `local.cliproxy` works

Instead of storing a bearer token in `opencode.json`, the plugin fetches the local proxy key at runtime by shelling out to a small helper script (`~/.local/bin/cliproxyapi-key`). With that key, it polls `http://127.0.0.1:8317/v1/models` every 60 seconds to get the list of prefixed routes currently active in CLIProxyAPI (like `claude-work/claude-sonnet-5-5` or `codex-personal/gpt-6.1-sol`).

The catch with `/v1/models` is that it only returns model IDs. It says nothing about context windows, tool-calling support, or reasoning effort variants.

To fill those in, the plugin uses `ctx.provider.transform`. For each route returned by the proxy, it strips the account prefix (`claude-work/`), looks up the base model (`claude-sonnet-5-5`) in OpenCode's built-in `anthropic` or `openai` catalog, and clones its metadata into a new per-account provider:

```ts
await ctx.provider.transform((editor) => {
  for (const account of accounts) {
    const providerID = Provider.ID.make(`cliproxy-${account.id}`)
    const source = editor.get(account.provider)
    const models: Model.Info[] = []

    for (const route of inventory) {
      if (!route.startsWith(`${account.id}/`)) continue
      const modelID = route.slice(account.id.length + 1)
      const template = source?.models.get(modelID)

      // Skip unknown models or models without tool support
      if (!template || !template.capabilities.tools) continue

      models.push({
        ...template,
        id: Model.ID.make(modelID),
        providerID,
        modelID: route,
        name: `${template.name} (${account.id})`,
        body: { ...template.body, model: route },
        package: account.provider === "anthropic"
          ? "@opencode/ai/providers/anthropic-compatible"
          : "@opencode/ai/providers/openai-compatible/responses",
      })
    }

    editor.add({
      info: {
        ...Provider.Info.empty(providerID),
        name: `CLIProxy / ${account.id}`,
        canonical: Provider.ID.make(account.provider),
        activation: "enabled",
        package: account.provider === "anthropic"
          ? "@opencode/ai/providers/anthropic-compatible"
          : "@opencode/ai/providers/openai-compatible/responses",
        settings,
      },
      models,
    })
  }
})
```

This is what makes the setup feel native. OpenCode sees a normal model ID under a dedicated provider for each account:

```text
cliproxy-claude-work/claude-sonnet-5-5
cliproxy-claude-personal/claude-sonnet-5-5
cliproxy-codex-work/gpt-6.1-sol
cliproxy-codex-personal/gpt-6.1-sol
```

Meanwhile, `body.model` (along with any reasoning variants cloned from the template) is rewritten to the full `claude-work/claude-sonnet-5-5` string that CLIProxyAPI expects on the wire. Claude accounts get wired to `@opencode/ai/providers/anthropic-compatible` (Anthropic Messages API), and Codex accounts use `@opencode/ai/providers/openai-compatible/responses` (OpenAI Responses API).

On each 60-second tick, the plugin compares the sorted model list against the previous snapshot and only calls `ctx.provider.reload()` when something actually changes. If the proxy is briefly unreachable during a restart, it catches the error and keeps the last known model inventory rather than wiping out the active providers.

## No silent failover

Because the proxy requires an explicit prefix on every request and the plugin never registers a pooled route, each provider is locked to a single credential. When an account hits a 429 rate limit, the proxy returns the error straight back to OpenCode without touching any other account.

Registering a separate provider per account also makes subagents nice to use. Because the provider IDs are descriptive (`cliproxy-claude-work`, `cliproxy-codex-personal`), I can just tell OpenCode in plain English which account a subagent should run on. The main agent maps that request to the right provider ID on its own, with no custom parsing needed in the plugin.

## Running it locally

CLIProxyAPI runs as a `systemd` user service that starts on login, with both its API and web UI bound to `localhost`. The OAuth tokens sit outside my dotfiles repo so I don't accidentally commit credentials to Git. (If you're setting it up, make sure the proxy binary is on V8+; the newer web UI won't talk to a V7 backend.)

The split works well in practice: CLIProxyAPI deals with auth and token lifecycles, and the OpenCode plugin turns each account into an explicit route I can pick deliberately.

Fin!
