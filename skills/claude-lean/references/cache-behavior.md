# Prompt Cache Behavior

## How Prompt Caching Works in Claude Code

Claude Code uses Anthropic's prompt caching to avoid re-processing the same system prompt and context on every turn. When cache hits, you get a 90% discount on those input tokens.

## What Gets Cached

The following components form the "cache prefix" — the stable part of the prompt that can be cached across turns:

1. **System prompt** (~20,000 tokens) — Claude Code's built-in instructions
2. **CLAUDE.md** — your configuration (global + project)
3. **MEMORY.md** — persistent memories
4. **MCP tool schemas** — definitions of available tools
5. **Skill metadata** — names and descriptions of installed skills

## Cache Hit Conditions

For a cache hit, the prefix must be **identical** to a previous request. Any change to the prefix invalidates the cache.

### What breaks the cache
- Changing the model (e.g., Opus → Sonnet)
- Connecting or disconnecting an MCP server
- Modifying CLAUDE.md or MEMORY.md
- Installing or removing a skill
- Session inactivity timeout

### Cache TTL (Time To Live)
- Free tier: 5 minutes of inactivity
- Paid subscribers: 1 hour of inactivity
- Enterprise/API: configurable

## Cost Math

Given pricing for Sonnet 4.6:
- Normal input: $3.00 / 1M tokens
- Cache read: $0.30 / 1M tokens (90% discount)
- Cache write: $3.75 / 1M tokens (25% premium)

For a 30,000-token prefix over 10 turns:
- Without cache: 30,000 * 10 * $3.00/1M = $0.90
- With cache: 30,000 * $3.75/1M (first write) + 30,000 * 9 * $0.30/1M (9 reads) = $0.1125 + $0.081 = $0.1935
- Savings: $0.71 (79%)

## Maximizing Cache Hits

### Do
- Keep your session model consistent
- Set up all MCPs before starting
- Send messages periodically during long thinking
- Use a stable CLAUDE.md (don't edit it during a session)

### Don't
- Switch between models mid-session
- Toggle MCP servers on and off
- Leave long gaps between messages
- Edit CLAUDE.md while working

## Monitoring Cache Performance

The Anthropic API response headers include cache hit information:
- `anthropic-cache-creation-input-tokens`: tokens written to cache
- `anthropic-cache-read-input-tokens`: tokens read from cache

Claude Code doesn't expose these directly, but the ratio of cache reads to total input tokens indicates cache health. A healthy session should see 80-95% cache hit rate after the first turn.
