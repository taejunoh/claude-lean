# Installing Claude Lean for Codex

## Prerequisites

- Git
- Python 3.9+ with pip

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/taejunoh/claude-lean.git ~/.codex/claude-lean
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/claude-lean/skills ~/.agents/skills/claude-lean
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\claude-lean" "$env:USERPROFILE\.codex\claude-lean\skills"
   ```

3. **Install tiktoken:**
   ```bash
   pip install tiktoken
   ```

4. **Restart Codex** to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/claude-lean
```

You should see a symlink pointing to the claude-lean skills directory.

## Updating

```bash
cd ~/.codex/claude-lean && git pull
```

## Uninstalling

```bash
rm ~/.agents/skills/claude-lean
rm -rf ~/.codex/claude-lean
```
