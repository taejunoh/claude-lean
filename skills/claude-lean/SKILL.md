---
name: claude-lean
description: >
  This skill activates automatically on session start when the SessionStart
  hook detects token issues (RED/YELLOW zone). Also trigger manually when
  the user asks to "check token usage", "optimize CLAUDE.md", "reduce costs",
  "measure tokens", "how much am I spending", or mentions "claude-lean",
  "/diagnose", "/optimize", "/benchmark", "cost analysis", "cache optimization",
  or asks about per-turn token counts. Trigger even when the user doesn't
  explicitly name the skill — any mention of Claude Code cost, context size,
  or config optimization should activate it.
metadata:
  version: "1.0.0"
  author: "Taejun"
---

# Claude Lean

Automatic token measurement, cost analysis, and optimization for Claude Code sessions.

## Auto-Run Behavior

The SessionStart hook injects a scan summary into every session. When you see that summary in context, act on it immediately:

- **RED zone** → Run the full optimization workflow below without being asked
- **YELLOW zone** → Mention the finding, show estimated savings, suggest optimizing
- **MCP warning** → Note the overhead, suggest disabling unused servers
- **All clear** → Briefly confirm. No action needed.

This is the core design: measure automatically, act proactively, confirm with the user before applying changes.

## Optimization Workflow

### Phase 1: Measure (automatic)

The hook already ran `count_tokens.py scan` and injected results. If you need more detail:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/count_tokens.py scan --format json
```

### Phase 2: Classify with LLM Review

The Python optimizer does a first pass using pattern matching:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py ~/.claude/CLAUDE.md --format json
```

This produces a section-by-section classification. However, pattern matching is mechanical — it can't understand context. Your job is to **review and override** the classifications using your judgment.

For each section the script classifies, evaluate:

1. **Is this actually used every conversation?** Rules like "use 2-space indent" = essential. A code example showing the pattern = maybe essential too, even though the regex flags it as "movable" because it's long.

2. **Would Claude need this without being asked?** If yes → essential. If only when working on a specific task → movable to refs/.

3. **Is this stale or redundant?** Incident logs from 6 months ago, meeting notes, deprecated instructions → removable.

Override the script's classification when your judgment differs. Present the final classification to the user as a table:

```
Section                  | Tokens | Script Says | Your Call  | Reason
-------------------------|--------|-------------|------------|-------
Coding Style             |    120 | essential   | essential  | Used every turn
API Endpoints Table      |    850 | movable     | movable    | Only needed for API work
Auth Code Example        |    340 | movable     | essential  | Critical pattern, referenced often
Incident Log Dec 2024    |    280 | removable   | removable  | Historical, stale
```

### Phase 3: Confirm and Apply

After presenting the classification, ask the user:
- "Should I apply these changes? (CLAUDE.md sections marked 'movable' will be split to refs/, 'removable' will be archived)"

Only after explicit confirmation:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py ~/.claude/CLAUDE.md --apply --backup
```

If you overrode any classifications, apply those manually with Edit tool instead of running the script blindly.

### Phase 4: Verify

Run benchmark to show the improvement:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py --before <backup_path> --after ~/.claude/CLAUDE.md
```

Present the before/after comparison: tokens saved, cost reduction per model, accuracy verification.

## Manual Commands

These still work for on-demand use:

- `/diagnose` — Full scan + cost estimate
- `/optimize [path]` — Analyze and optimize a specific file
- `/benchmark [before] [after]` — Compare two files

## Scripts Reference

All in `${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/`:

| Script | Purpose |
|--------|---------|
| `count_tokens.py scan` | Scan all Claude config files, measure tokens |
| `count_tokens.py count <path>` | Measure specific files |
| `analyze_cost.py --scan` | Estimate session costs from scan |
| `optimize_claude_md.py <file>` | Classify sections (dry-run) |
| `optimize_claude_md.py <file> --apply` | Apply optimizations |
| `benchmark.py <file>` | Simulate before/after |
| `benchmark.py --before A --after B` | Compare two files |
| `generate_report.py -o <path>` | Full markdown report |

## Grading

- **GREEN** (<750 tokens): Lean. No action.
- **YELLOW** (750–2,000 tokens): Consider splitting.
- **RED** (>2,000 tokens): Auto-optimize.

## Key Principles

Read `references/optimization-rules.md` for the full playbook. Read `references/pricing.md` for model costs. Read `references/cache-behavior.md` for cache mechanics.
