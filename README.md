# Claude Lean

Accurate token measurement, cost analysis, auto-optimization, and benchmarking for your coding agent sessions.

## How it works

Every turn in Claude Code replays your system prompt, CLAUDE.md, MEMORY.md, MCP schemas, and skill metadata. A bloated config quietly burns tokens — and money — on every single message.

Claude Lean measures exactly how much each component costs using **tiktoken-based counting** (not the rough "bytes / 4" guess), then helps you trim the fat.

When you start a session, it checks your setup and warns you if something looks heavy. You can run `/diagnose` anytime to get a full breakdown, `/optimize` to automatically split heavy sections out of CLAUDE.md, and `/benchmark` to verify the savings with real numbers.

## Installation

**Note:** Installation differs by platform. Claude Code and Cursor have built-in plugin systems. Codex and OpenCode require manual setup.

### Claude Code (Manual Setup)

1. Clone the repo:

```bash
git clone https://github.com/taejunoh/claude-lean.git ~/.claude/plugins/claude-lean
```

2. Copy slash commands:

```bash
cp ~/.claude/plugins/claude-lean/commands/*.md ~/.claude/commands/
```

3. Add the SessionStart hook to `~/.claude/settings.json`. Merge this into your existing settings (keep your current keys, add the `hooks` section):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "CLAUDE_PLUGIN_ROOT=~/.claude/plugins/claude-lean ~/.claude/plugins/claude-lean/hooks/session-start"
          }
        ]
      }
    ]
  }
}
```

4. Append the plugin's CLAUDE.md content to your global config:

```bash
cat ~/.claude/plugins/claude-lean/CLAUDE.md >> ~/.claude/CLAUDE.md
```

5. Install tiktoken:

```bash
pip install tiktoken
```

### Claude Code (Marketplace) — Coming Soon

> **Coming Soon** — claude-lean will be available on the official marketplace. For now, use the manual setup above.
>
> ```bash
> /plugin install claude-lean@claude-plugins-official
> ```

### Cursor

In Cursor Agent chat:

```text
/add-plugin claude-lean
```

Or search for "claude-lean" in the plugin marketplace.

### Codex

Tell Codex:

```
Fetch and follow instructions from https://raw.githubusercontent.com/taejunoh/claude-lean/refs/heads/main/.codex/INSTALL.md
```

**Detailed docs:** [.codex/INSTALL.md](.codex/INSTALL.md)

### OpenCode

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/taejunoh/claude-lean/refs/heads/main/.opencode/INSTALL.md
```

**Detailed docs:** [.opencode/INSTALL.md](.opencode/INSTALL.md)

### Gemini CLI

```bash
gemini extensions install https://github.com/taejunoh/claude-lean
```

### Verify Installation

Start a new session and run `/diagnose`. You should see a token breakdown table with per-component measurements.

## Commands

| Command | What it does |
|---------|-------------|
| `/diagnose` | Scan all config files, measure tokens, estimate costs |
| `/optimize [path]` | Classify CLAUDE.md sections and split heavy content to refs/ |
| `/benchmark [before] [after]` | Compare before/after with verified token counts and cost savings |

## The Workflow

1. **Diagnose** — Run `/diagnose` to see where your tokens are going. Each component gets a GREEN/YELLOW/RED grade.

2. **Optimize** — If CLAUDE.md is in YELLOW or RED, run `/optimize`. It classifies each section as essential (keep), movable (split to refs/), or removable (archive). Always creates a backup first.

3. **Benchmark** — Run `/benchmark` to see the before/after comparison. Shows tiktoken-measured token counts, per-model cost savings, and how much more accurate tiktoken is versus naive byte estimation.

## What's Inside

### Skills
- **claude-lean** — Full diagnostic and optimization skill with 5 Python scripts

### Commands
- **diagnose** — Quick token scan and cost estimate
- **optimize** — CLAUDE.md analysis and auto-optimization
- **benchmark** — Before/after comparison with verified data

### Hooks
- **SessionStart** — Checks CLAUDE.md size and MCP count on startup, warns if overweight

### Scripts
| Script | Purpose |
|--------|---------|
| `count_tokens.py` | tiktoken-based token counter with language-aware fallback |
| `analyze_cost.py` | Per-model cost estimation with cache scenarios |
| `optimize_claude_md.py` | Section classifier and auto-optimizer |
| `benchmark.py` | Before/after comparison runner |
| `generate_report.py` | Comprehensive markdown report generator |

### References
| Doc | Contents |
|-----|----------|
| `pricing.md` | Model pricing table, cost multipliers, env vars |
| `optimization-rules.md` | Complete optimization playbook with checklist |
| `cache-behavior.md` | Prompt cache mechanics and best practices |

## Why tiktoken over bytes/4?

The naive "bytes / 4" method can be off by 40-80% for non-ASCII text (Korean, Japanese, emoji, code with lots of symbols). tiktoken's `cl100k_base` encoding closely approximates Claude's tokenizer and is typically within 5-15% of actual counts. The benchmark command shows both measurements side by side so you can see the difference.

## Running Tests

```bash
cd skills/claude-lean/scripts
pip install tiktoken pytest
python -m pytest tests/test_all.py -v
```

28 test cases covering token counting, cost analysis, optimizer logic, and benchmark runner.

## Updating

Manual update:

```bash
cd ~/.claude/plugins/claude-lean && git pull
cp commands/*.md ~/.claude/commands/
```

Once the marketplace is available:

```bash
/plugin update claude-lean
```

## Philosophy

- **Measure, don't guess** — tiktoken over byte division
- **Show your work** — benchmarks compare both methods side by side
- **Automate safely** — always backup before optimizing
- **Stay lean** — the plugin itself follows its own advice

## License

MIT

## Support

- **Issues**: https://github.com/taejunoh/claude-lean/issues
