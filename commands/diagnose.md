---
description: Scan token consumption and estimate session costs
allowed-tools: Read, Bash, Glob, Grep
---

Run a full token diagnostic for the user's Claude Code configuration.

1. First, check if tiktoken is installed:
   ```bash
   python3 -c "import tiktoken" 2>/dev/null || pip install tiktoken --break-system-packages -q
   ```

2. Run the token scanner:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/count_tokens.py" scan --format table
   ```

3. Run cost analysis based on the scan:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/analyze_cost.py" --scan --turns 10 --format table
   ```

4. Present results clearly with:
   - Per-component token breakdown with GREEN/YELLOW/RED grades
   - Cost estimates for Haiku, Sonnet, Opus (cached vs uncached)
   - Top 3 actionable optimization suggestions based on what was found

Keep output concise. If CLAUDE.md is in RED zone, recommend running `/optimize`.
