# Claude Model Pricing Reference

Last updated: 2025-Q4

## Pricing Table (per 1M tokens)

| Model | Input | Output | Cache Read | Cache Write |
|-------|-------|--------|------------|-------------|
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.10 | $1.25 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.30 | $3.75 |
| Claude Opus 4.6 | $15.00 | $75.00 | $1.50 | $18.75 |
| Claude Opus 4.6 (Fast) | $30.00 | $150.00 | $3.00 | $37.50 |

## Cost Multipliers

Relative to Sonnet 4.6 (baseline = 1x):

| Model | Input Cost | Output Cost |
|-------|-----------|-------------|
| Haiku 4.5 | 0.33x | 0.33x |
| Sonnet 4.6 | 1x | 1x |
| Opus 4.6 | 5x | 5x |
| Opus 4.6 Fast | 10x | 10x |

## Cache Economics

Prompt caching provides a 90% discount on cached input tokens. The tradeoff is a 25% premium on the first write to cache.

Break-even point: if you reuse the same prompt across 2+ turns, caching saves money.

For a typical 10-turn session with 90% cache hit rate:
- Haiku: saves ~$0.002 per session
- Sonnet: saves ~$0.006 per session
- Opus: saves ~$0.03 per session
- Opus Fast: saves ~$0.06 per session

The savings scale linearly with session length and input token count.

## Model Selection Guide

| Task Type | Recommended | Reason |
|-----------|-------------|--------|
| File reading, grep, simple edits | Sonnet | 5x cheaper, sufficient quality |
| Architecture, complex debugging | Opus | Deep reasoning needed |
| Template-based structured work | Sonnet | Framework handles the logic |
| Large code generation | Sonnet | Output tokens drive cost |
| Quick questions, formatting | Haiku | 15x cheaper than Opus |

## Environment Variables for Cost Control

```bash
# Force subagents to use Sonnet (saves 5x on subagent calls)
export CLAUDE_CODE_SUBAGENT_MODEL="claude-sonnet-4-6"

# Disable 1M context (force 200K, more aggressive compression)
export CLAUDE_CODE_DISABLE_1M_CONTEXT=1

# Limit file read output tokens (default 25K)
export CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=10000
```
