# AnomalyArmor Agents Development Guide

This document provides development guidelines for contributing to the AnomalyArmor agents repository.

## Repository Structure

```
anomalyarmor/agents/
├── .claude-plugin/
│   └── marketplace.json      # Claude plugin manifest
├── skills/                   # Skill definitions (markdown)
│   ├── status/SKILL.md       # Health check skill
│   ├── alerts/SKILL.md       # Alert management skill
│   ├── connect/SKILL.md      # Data source connection skill
│   ├── monitor/SKILL.md      # Monitoring setup skill
│   ├── ask/SKILL.md          # Natural language Q&A skill
│   ├── analyze/SKILL.md      # Intelligence gathering skill
│   └── start/SKILL.md        # Guided onboarding wizard
├── armor-mcp/                # MCP server package
│   ├── src/armor_mcp/
│   │   ├── server.py         # FastMCP server
│   │   └── tools/            # MCP tools (organized by domain)
│   ├── pyproject.toml
│   └── tests/
├── scripts/
│   ├── ensure-auth.py        # Authentication validation hook
│   └── skill-suggester.sh    # Skill suggestion hook
├── AGENTS.md                 # This file
├── CLAUDE.md                 # Symlink to AGENTS.md
├── LICENSE
└── README.md
```

## Architecture

### Skills vs MCP Server

These are **independent delivery mechanisms**:

- **Skills**: Markdown instructions that tell Claude to write Python code using the SDK directly. Used via `/armor:status`, `/armor:alerts`, etc.
- **MCP Server**: Structured tools for any MCP client (Claude Code, Cursor, etc.). Provides programmatic access to the SDK.

Both use the same underlying `anomalyarmor` Python SDK but can be used independently.

### Skill Format

Skills use YAML frontmatter in `skills/<name>/SKILL.md`:

```yaml
---
name: armor-status
description: Check data health, alerts, freshness issues, schema changes.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Skill Title

## Prerequisites
- Requirements...

## Steps
1. Step one...

## Example Usage
```python
# Code example
```
```

### MCP Server Pattern

Tools follow a consistent pattern using the `sdk_tool` decorator:

```python
@mcp.tool()
@sdk_tool
def tool_name(param: str):
    """Tool description."""
    return _get_client().resource.method(param)
```

## Development

### Prerequisites

- Python 3.11+
- uv (for package management)
- anomalyarmor SDK (`pip install anomalyarmor`)

### Running MCP Server Locally

```bash
cd armor-mcp
uv run armor-mcp
```

### Testing

```bash
cd armor-mcp
uv run pytest
```

### Adding a New Skill

1. Create `skills/<name>/SKILL.md`
2. Add YAML frontmatter with name, description, and hooks
3. Write step-by-step instructions
4. Include working code examples
5. Test with Claude Code

### Adding a New MCP Tool

1. Add tool function in appropriate `tools/*.py` module
2. Use `@mcp.tool()` and `@sdk_tool` decorators
3. Mirror SDK method signature
4. Add docstring with Args section
5. Register in `server.py` imports
6. Add test in `tests/`

## Code Style

- Follow SDK method signatures exactly
- Use type hints
- Include docstrings with Args sections
- Handle errors gracefully (sdk_tool decorator handles this)
- Keep tools focused and single-purpose

## Testing Skills

1. Install plugin: `claude plugin install armor@anomalyarmor`
2. Or add skills: `npx skills add anomalyarmor/agents`
3. Run skill: `/armor:status`
4. Verify output matches expected behavior

## Release Process

1. Update version in `armor-mcp/pyproject.toml`
2. Update version in `.claude-plugin/marketplace.json`
3. Create GitHub release
4. Publish to PyPI: `cd armor-mcp && uv publish`
