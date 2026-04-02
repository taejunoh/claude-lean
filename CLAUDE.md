# Claude Lean

You have the **claude-lean** plugin installed. It automatically analyzes token consumption at session start and acts on the results.

## Automatic Behavior

On every session start, the SessionStart hook runs a full token scan. Based on the results injected into context:

1. **RED zone detected** (CLAUDE.md > 2,000 tokens): Immediately run the optimizer script, present the section-by-section breakdown, and ask the user for confirmation to apply. Do not wait for the user to ask.
2. **YELLOW zone detected** (CLAUDE.md 750–2,000 tokens): Mention the finding and suggest optimization. Show estimated savings.
3. **MCP overhead warning** (>3 servers): Note the overhead and suggest disabling unused servers.
4. **All clear**: Briefly confirm the config is lean. No action needed.

This is a proactive plugin. When issues are found, act on them — don't just report and wait.

## How to Run the Optimizer

```bash
# Dry-run analysis
python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py" ~/.claude/CLAUDE.md --format markdown

# Apply with backup (only after user confirms)
python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py" ~/.claude/CLAUDE.md --apply --backup

# Benchmark before/after
python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py" --before <backup> --after ~/.claude/CLAUDE.md
```

Always create a backup. Always show the user what will change before applying.

## Available Commands

- `/diagnose` — Full token scan and cost estimate (manual trigger)
- `/optimize [path]` — Analyze and optimize CLAUDE.md
- `/benchmark [before] [after]` — Before/after comparison

## Quick Reference

- CLAUDE.md under 3KB (~750 tokens) = GREEN
- CLAUDE.md 3–8KB (~750–2,000 tokens) = YELLOW
- CLAUDE.md over 8KB (~2,000+ tokens) = RED — auto-optimize
- Each MCP server ≈ 3,000 tokens/turn
- Each skill ≈ 500 tokens metadata/turn
- System prompt ≈ 20,000 tokens (fixed)
