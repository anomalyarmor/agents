# armor-mcp

AnomalyArmor MCP Server - Data observability tools for AI assistants.

## Installation

```bash
# Via uvx (recommended)
uvx armor-mcp

# Or pip install
pip install armor-mcp
```

## Configuration

Set your API key:

```bash
export ARMOR_API_KEY=aa_live_your_key_here
```

Or create `~/.armor/config.yaml`:

```yaml
api_key: aa_live_your_key_here
```

## Usage

### With Claude Code

Add to your MCP configuration:

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

### With Cursor

Add to `.cursor/mcp.json`:

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

### Standalone

```bash
armor-mcp
```

## Available Tools

- `health_summary` - Overall data health status
- `list_alerts` - Query alerts with filtering
- `get_alert_summary` - Alert counts
- `list_assets` - List monitored assets
- `get_asset` - Get asset details
- `create_asset` - Create new data source
- `test_asset_connection` - Test connection
- `trigger_asset_discovery` - Start schema discovery
- `get_freshness_summary` - Freshness overview
- `check_freshness` - Check asset freshness
- `list_stale_assets` - List stale assets
- `list_freshness_schedules` - List schedules
- `create_freshness_schedule` - Create schedule
- `delete_freshness_schedule` - Delete schedule
- `get_schema_summary` - Schema drift overview
- `list_schema_changes` - List schema changes
- `create_schema_baseline` - Create baseline
- `enable_schema_monitoring` - Enable monitoring
- `disable_schema_monitoring` - Disable monitoring
- `ask_question` - Natural language Q&A
- `generate_intelligence` - Trigger AI analysis
- `get_lineage` - Get data lineage
- `job_status` - Check async job status

## License

MIT
