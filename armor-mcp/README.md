# armor-mcp

[![PyPI](https://img.shields.io/pypi/v/armor-mcp.svg)](https://pypi.org/project/armor-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/anomalyarmor/agents/blob/main/LICENSE)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-blue)](https://modelcontextprotocol.io)

The **AnomalyArmor MCP server** lets AI assistants (Claude Code, Cursor, Claude Desktop, any MCP client) interact with your data warehouse through 50+ structured tools: query alerts, monitor freshness, investigate schema drift, configure validity rules, and trace lineage in natural language.

- **Homepage**: <https://www.anomalyarmor.ai>
- **Docs**: <https://docs.anomalyarmor.ai/integrations/mcp-server>
- **Server card**: <https://www.anomalyarmor.ai/.well-known/mcp/server-card.json>
- **Status**: Production. Versioned MCP protocol `2025-06-18`. OAuth 2.1 + API key auth.

## Two ways to connect

| Method | Auth | Best for |
|--------|------|----------|
| **Remote (recommended)** | OAuth 2.1 (Clerk) | Zero install, always up to date |
| **Local** | API key | Air-gapped, on-call laptops, custom proxies |

## Remote (recommended)

The server is hosted at `https://mcp.anomalyarmor.ai/mcp` (Streamable HTTP transport). First call opens a browser for OAuth; the token is cached for ~12h.

### Claude Code

```bash
claude mcp add anomalyarmor --transport http https://mcp.anomalyarmor.ai/mcp
```

### Cursor

Add to `~/Library/Application Support/Cursor/mcp.json` (macOS), `~/.config/Cursor/mcp.json` (Linux), or `%APPDATA%\Cursor\mcp.json` (Windows):

```json
{
  "mcpServers": {
    "anomalyarmor": {
      "url": "https://mcp.anomalyarmor.ai/mcp"
    }
  }
}
```

### Any MCP client

```
URL: https://mcp.anomalyarmor.ai/mcp
Transport: streamable-http
Auth: OAuth 2.1
Discovery: https://mcp.anomalyarmor.ai/.well-known/oauth-protected-resource
```

## Local (API key)

Use when the remote server isn't reachable or when you want no third-party dependency.

### Install

```bash
# Recommended: uvx (no install)
uvx armor-mcp

# Or pip
pip install armor-mcp
```

### Configure

Get an API key from **Settings → API Keys** at <https://app.anomalyarmor.ai>.

```bash
export ARMOR_API_KEY=aa_live_your_key_here
```

Or persist to `~/.armor/config.yaml`:

```yaml
api_key: aa_live_your_key_here
```

### Wire to a client

```json
{
  "mcpServers": {
    "anomalyarmor": {
      "command": "uvx",
      "args": ["armor-mcp"],
      "env": {
        "ARMOR_API_KEY": "aa_live_your_key_here"
      }
    }
  }
}
```

## Tools

53 tools across 8 categories. Every tool ships with MCP `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint: false`) so hosts can decide when to auto-confirm.

### Health & Briefings

| Tool | Description |
|------|-------------|
| `health_summary` | Overall warehouse health: stale assets, drift, alerts |
| `get_todays_briefing` | Daily digest with key insights |
| `get_coverage` | Monitoring coverage analysis |
| `manage_coverage` | Update coverage targets |
| `recommend` | AI-suggested next monitoring actions |

### Alerts & Incidents

| Tool | Description |
|------|-------------|
| `list_alerts` | Query alerts with filters (severity, date, status) |
| `list_inbox_alerts` | Alerts not yet triaged |
| `get_alerts_summary` | Aggregate counts and trends |
| `get_alert_trends` | Period-over-period trend analysis |
| `get_alert_history` | Activity timeline for an alert |
| `update_alert` | Acknowledge / resolve / dismiss / snooze |
| `list_alert_rules` | View configured rules |
| `create_alert_rule` | Add a new alert rule |
| `manage_alert_rule` | Update / delete / preview rules |
| `manage_rule_destinations` | Wire rules to destinations |

### Assets

| Tool | Description |
|------|-------------|
| `list_assets` | List data sources with filters |
| `create_asset` | Connect a new source |
| `manage_asset` | Update / delete / test connection |
| `trigger_asset_discovery` | Start schema discovery (async) |

### Freshness

| Tool | Description |
|------|-------------|
| `get_freshness_summary` | Freshness overview |
| `check_freshness` | Check a specific asset / table |
| `setup_freshness` | Bulk-create freshness schedules |
| `list_freshness_schedules` | View configured schedules |
| `manage_freshness_schedule` | Update / delete a schedule |

### Schema Monitoring

| Tool | Description |
|------|-------------|
| `get_schema_summary` | Drift overview |
| `list_schema_changes` | Recent changes with severity |
| `create_schema_baseline` | Capture current schema as a baseline |
| `enable_schema_monitoring` | Start drift detection |
| `disable_schema_monitoring` | Stop drift detection |

### Data Quality (Metrics & Validity)

| Tool | Description |
|------|-------------|
| `get_metrics_summary` | Metric health by asset |
| `list_metrics` | List configured metrics |
| `create_metric` | Add a metric (row count, null %, etc.) |
| `manage_metric` | Update / delete / capture a metric |
| `get_validity_summary` | Pass/fail rate for validity rules |
| `list_validity_rules` | List validity rules |
| `create_validity_rule` | Add a NOT_NULL / UNIQUE / RANGE / REGEX rule |
| `manage_validity_rule` | Update / delete / run a rule |
| `create_referential_check` | Cross-table referential check |
| `manage_referential` | Update / delete a referential check |

### Destinations & Routing

| Tool | Description |
|------|-------------|
| `list_destinations` | Slack / email / webhook / PagerDuty configs |
| `setup_destination` | Add a new destination |
| `manage_destination` | Update / delete / test |

### Intelligence, Lineage, Tags, Jobs

| Tool | Description |
|------|-------------|
| `ask_question` | Synchronous natural-language Q&A about your data |
| `generate_intelligence` | Trigger AI analysis (async, expensive) |
| `get_lineage` | Upstream/downstream dependency graph |
| `list_tags` | Tags for an asset |
| `create_tag` | Tag a table or column |
| `apply_tags` | Bulk tag application |
| `job_status` | Track an async job |
| `cancel_job` | Cancel a running async job |
| `get_api_key_info` | Inspect the current API key's scope |

Full descriptions, parameter schemas, and example prompts: <https://docs.anomalyarmor.ai/integrations/mcp-server>.

## Tool safety conventions

Hosts respect the annotations:

| Category | Pattern | Confirmation |
|----------|---------|--------------|
| Read-only | `list_*`, `get_*`, `check_*`, `search_*` | Auto-invoke |
| Mutating | `create_*`, `update_*`, `enable_*`, `disable_*`, `manage_*` | Confirm with user |
| Destructive | `delete_*` (via `manage_*`), `dismiss_alert` | Always confirm; list affected entities |
| Expensive | `generate_intelligence`, `trigger_asset_discovery` | Confirm; these queue paid jobs |

## Multi-tenancy

The OAuth token (or API key) is scoped to the user's company. You cannot impersonate another tenant. Don't fabricate `company_id` arguments.

## Async jobs

`trigger_asset_discovery`, `generate_intelligence`, and metric captures return a `job_id`. Poll with `job_status(job_id)` rather than re-triggering.

## Discovery surfaces

| File | Purpose |
|------|---------|
| `https://mcp.anomalyarmor.ai/.well-known/oauth-protected-resource` | RFC 9728 protected-resource metadata |
| `https://www.anomalyarmor.ai/.well-known/mcp/server-card.json` | SEP-1649 MCP server card |
| `https://www.anomalyarmor.ai/.well-known/agent-card.json` | A2A v0.2 agent card |
| `https://www.anomalyarmor.ai/.well-known/api-catalog` | RFC 9727 API catalog linkset |

## Development

```bash
git clone https://github.com/anomalyarmor/agents.git
cd agents/armor-mcp
uv sync
uv run pytest
```

## License

MIT — see [LICENSE](https://github.com/anomalyarmor/agents/blob/main/LICENSE).
