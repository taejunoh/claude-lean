---
description: Analyze and optimize CLAUDE.md to reduce token consumption
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [path-to-claude-md]
---

Analyze and optimize a CLAUDE.md file to reduce per-turn token consumption.

Target file: $1 (defaults to ~/.claude/CLAUDE.md if not specified)

1. First, check if tiktoken is installed:
   ```bash
   python3 -c "import tiktoken" 2>/dev/null || pip install tiktoken --break-system-packages -q
   ```

2. Run the optimizer in dry-run mode first to show what would change:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py" "$1" --format markdown
   ```
   If $1 is empty, use `~/.claude/CLAUDE.md`.

3. Present the analysis to the user:
   - Show section-by-section classification (essential / movable / removable)
   - Show token reduction potential
   - Show estimated cost savings

4. Ask the user if they want to apply the optimizations.

5. If they confirm, apply with backup:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/optimize_claude_md.py" "$1" --apply --backup
   ```

6. After applying, run a quick before/after comparison:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py" --before <backup_path> --after "$1" --format table
   ```

Always create a backup before modifying files. Never apply without explicit user confirmation.
