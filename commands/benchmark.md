---
description: Compare token counts and costs before and after optimization
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [before-file] [after-file]
---

Run a benchmark comparing token consumption before and after optimization.

Arguments:
- $1: "before" file path (original CLAUDE.md or config)
- $2: "after" file path (optimized version)

If no arguments given, auto-detect from current CLAUDE.md and simulate optimization.

1. First, check if tiktoken is installed:
   ```bash
   python3 -c "import tiktoken" 2>/dev/null || pip install tiktoken --break-system-packages -q
   ```

2. Run the benchmark:
   ```bash
   # With explicit before/after files
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py" --before "$1" --after "$2" --turns 10

   # Or auto-detect mode
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py" ~/.claude/CLAUDE.md --turns 10
   ```

3. Present results with:
   - Token reduction (tiktoken-measured, not byte-estimated)
   - Accuracy comparison: tiktoken vs naive (bytes/4) to show measurement improvement
   - Per-model cost savings table (Haiku, Sonnet, Opus)
   - Cache vs no-cache scenarios

4. Optionally save full report:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-lean/scripts/benchmark.py" "$1" --output ~/.claude/claude-lean-benchmark.json
   ```

Highlight the accuracy difference between tiktoken and naive estimation to demonstrate why precise measurement matters.
