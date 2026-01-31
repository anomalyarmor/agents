# AnomalyArmor Agents

AI skills and MCP server for AnomalyArmor data observability. Interact with your data health, alerts, and monitoring directly from Claude Code, Cursor, or any MCP-compatible AI tool.

## Quick Start

### Option 1: Claude Code Plugin (Recommended)

```bash
# Install the plugin
claude plugin marketplace add anomalyarmor/agents
claude plugin install armor@anomalyarmor

# Or via skills.sh
npx skills add anomalyarmor/agents
```

Then use skills like:
- `/armor:status` - Check data health
- `/armor:alerts` - View and manage alerts
- `/armor:ask` - Ask questions about your data

### Option 2: MCP Server

Add to your MCP configuration (Claude Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "armor": {
      "command": "uvx",
      "args": ["armor-mcp"]
    }
  }
}
```

## Prerequisites

1. **AnomalyArmor Account**: Sign up at [anomalyarmor.ai](https://anomalyarmor.ai)
2. **API Key**: Generate at Settings > API Keys
3. **Configure**: Set `ARMOR_API_KEY` env var or create `~/.armor/config.yaml`:

```yaml
api_key: aa_live_your_key_here
```

## Available Skills

| Skill | Description | Example |
|-------|-------------|---------|
| `/armor:status` | Health summary across all assets | "Is my data healthy?" |
| `/armor:alerts` | Query and manage alerts | "What alerts fired yesterday?" |
| `/armor:connect` | Connect a new data source | "Connect my Snowflake warehouse" |
| `/armor:monitor` | Set up monitoring | "Monitor freshness for orders table" |
| `/armor:ask` | Natural language Q&A | "What tables contain customer data?" |
| `/armor:analyze` | Trigger AI analysis | "Analyze the finance schema" |
| `/armor:start` | Guided onboarding | "Get me started with AnomalyArmor" |

## MCP Tools

The MCP server exposes these tools:

### Health
- `health_summary()` - Overall health status

### Alerts
- `list_alerts(status, severity, asset_id, from_date, to_date)` - Query alerts
- `get_alert_summary()` - Alert counts

### Assets
- `list_assets(source, asset_type, search)` - List monitored assets
- `get_asset(asset_id)` - Get asset details
- `create_asset(name, source_type, connection_config)` - Create data source
- `test_asset_connection(asset_id)` - Test connection
- `trigger_asset_discovery(asset_id)` - Start schema discovery

### Freshness
- `get_freshness_summary()` - Freshness overview
- `check_freshness(asset_id)` - Check specific asset
- `list_stale_assets()` - List stale assets
- `list_freshness_schedules(asset_id)` - List schedules
- `create_freshness_schedule(asset_id, table_path, check_interval)` - Create schedule
- `delete_freshness_schedule(schedule_id)` - Delete schedule

### Schema
- `get_schema_summary()` - Schema drift overview
- `list_schema_changes(asset_id, severity)` - List changes
- `create_schema_baseline(asset_id)` - Create baseline
- `enable_schema_monitoring(asset_id, schedule_type)` - Enable monitoring
- `disable_schema_monitoring(asset_id)` - Disable monitoring

### Intelligence
- `ask_question(asset, question)` - Natural language Q&A
- `generate_intelligence(asset)` - Trigger AI analysis

### Lineage
- `get_lineage(asset_id, depth, direction)` - Get lineage graph

### Jobs
- `job_status(job_id)` - Check async job status

## Examples

### Check Data Health

```
User: Is my data healthy?
Claude: [Runs /armor:status]

Your data health status:
- Overall: WARNING
- 3 unresolved alerts
- 2 stale tables (orders, customers)
- 1 unacknowledged schema change
```

### Query Alerts

```
User: What alerts fired yesterday?
Claude: [Runs /armor:alerts]

Yesterday's alerts:
1. [CRITICAL] orders table stale for 6 hours
2. [WARNING] schema change detected in users table
3. [INFO] new column added to products
```

### Ask About Data

```
User: What tables contain customer PII?
Claude: [Runs /armor:ask]

Based on AnomalyArmor Intelligence:
- customers.email (PII: email)
- customers.phone (PII: phone)
- orders.shipping_address (PII: address)
```

## Troubleshooting

### Authentication Failed

```
Error: No API key configured
```

**Solution**: Set `ARMOR_API_KEY` environment variable or create `~/.armor/config.yaml`

### MCP Server Not Found

```
Error: MCP server 'armor' not found
```

**Solution**:
1. Restart your AI tool after config changes
2. Verify uvx is installed: `uvx --version`
3. Check MCP config syntax

### Skills Not Loading

**Solution**:
1. Verify plugin installed: `claude plugin list`
2. Check skills directory exists
3. Restart Claude Code

## Development

See [AGENTS.md](AGENTS.md) for development guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/anomalyarmor/agents/issues)
- **Docs**: [docs.anomalyarmor.ai](https://docs.anomalyarmor.ai)
- **Email**: support@anomalyarmor.ai

## License

MIT License - see [LICENSE](LICENSE)
