# Optimization Rules

## Rule 1: Keep CLAUDE.md Under 3KB

CLAUDE.md is loaded into context on every single turn. A 20KB CLAUDE.md means ~5,000 tokens consumed per turn before you even type anything.

Target: under 3KB (~750 tokens).

### What belongs in CLAUDE.md
- Coding style rules (indent, naming conventions)
- Output format preferences
- Behavioral directives (always/never rules)
- Project-specific constraints that apply to every task

### What to move out
Move to `.claude/rules/` (loaded selectively) or `refs/` (loaded on demand):

- Code examples longer than 3 lines
- UUID/ID reference tables
- Deployment commands and scripts
- Full API endpoint lists
- Incident/postmortem records
- Environment-specific configurations
- Team/org charts
- Detailed workflow descriptions

### The refs/ pattern
Create a `refs/` directory alongside CLAUDE.md. Move heavy content there and add a comment in CLAUDE.md:

```markdown
<!-- API reference: see refs/api-endpoints.md -->
<!-- Deployment guide: see refs/deploy.md -->
```

Claude can read these files on demand when needed, instead of loading them every turn.

## Rule 2: Manage MCP Servers

Each active MCP server adds approximately 3,000 tokens of schema to every turn (tool definitions, parameter schemas, descriptions).

5 MCP servers = ~15,000 extra tokens per turn.

### Actions
- Disable MCP servers you aren't actively using
- Set up project-specific MCP configs (`.mcp.json` in project root)
- Review server schemas — some servers expose many unused tools

## Rule 3: Choose the Right Model

Not every task needs Opus. A 10-turn session on Opus costs 5x what the same session costs on Sonnet.

### Decision framework
- Start with Sonnet as default
- Switch to Opus only for: architecture decisions, complex multi-file debugging, nuanced code review
- Use Haiku for: quick lookups, formatting, simple file operations

### Subagent model override
Set `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6` to force all subagent calls to use Sonnet. Most subagent tasks (file reading, grep, simple analysis) don't need Opus-level reasoning.

## Rule 4: Maintain Cache

Prompt caching gives you a 90% discount on repeated input tokens. But cache breaks easily:

### Cache-breaking events
- Switching models mid-session
- Connecting/disconnecting MCP servers
- 5+ minutes of inactivity (free tier) / 1 hour (paid)
- Changing system prompt content

### Cache maintenance habits
- Set up all MCPs before starting work
- Don't switch between Opus and Sonnet in the same session
- If you need to think, send a light message to keep the session alive
- Use `/clear` to start fresh rather than switching context back and forth

## Rule 5: Manage Context Growth

Claude Code conversations accumulate context over time. Long conversations become expensive because every turn replays the full history.

### Actions
- Use `/clear` when switching to a different task
- Use `/compact` for long conversations to compress history
- When reading files, specify `offset` and `limit` instead of reading entire files
- Set `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=10000` to cap file read output

## Rule 6: Optimize MEMORY.md

MEMORY.md is loaded every turn, just like CLAUDE.md. Keep it concise:

- Maximum 200 lines / 25KB
- Remove outdated entries
- Use terse, keyword-style notes rather than full sentences
- Archive old memories periodically

## Rule 7: Rules Directory Strategy

Files in `.claude/rules/` are selectively loaded based on relevance. Use this to your advantage:

- Move task-specific instructions to separate rule files
- Use descriptive filenames so Claude can pick the right one
- Keep each rule file focused on one topic
- Total rules should not exceed the equivalent of what you'd put in CLAUDE.md

## Optimization Checklist

Before starting a session, verify:

- [ ] CLAUDE.md is under 3KB
- [ ] Only needed MCP servers are enabled
- [ ] MEMORY.md is under 200 lines
- [ ] Rules directory has focused, small files
- [ ] Subagent model is set to Sonnet (if applicable)
- [ ] File read token limit is configured
