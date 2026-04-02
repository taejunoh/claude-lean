# Installing Claude Lean for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed
- Python 3.9+ with pip

## Installation

Add claude-lean to the `plugin` array in your opencode.json (global or project-level):

```json
{
  "plugin": ["claude-lean@git+https://github.com/taejunoh/claude-lean.git"]
}
```

Then install tiktoken:

```bash
pip install tiktoken
```

Restart OpenCode. The plugin auto-installs and registers all skills.

Verify by asking: "Diagnose my token usage"

## Version Pinning

```json
{
  "plugin": ["claude-lean@git+https://github.com/taejunoh/claude-lean.git#v1.0.0"]
}
```

## Updating

Restart OpenCode to pull the latest version. Or pin a specific version tag.

## Troubleshooting

### Plugin not loading

1. Check logs: `opencode run --print-logs "hello" 2>&1 | grep -i claude-lean`
2. Verify the plugin line in your opencode.json

### Scripts failing

Make sure tiktoken is installed: `pip install tiktoken`
