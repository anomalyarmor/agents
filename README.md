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
| `/armor:quality` | Data quality checks | "Add null check for customer_id column" |
| `/armor:tags` | Asset tagging and classification | "Tag this table as PII" |
| `/armor:investigate` | Root cause analysis | "Why is this table stale?" |
| `/armor:lineage` | Data lineage exploration | "What depends on this table?" |
| `/armor:profile` | Table profiling and stats | "Profile the orders table" |
| `/armor:coverage` | Monitoring coverage analysis | "What tables have no alerts?" |
| `/armor:test` | Dry-run configurations before enabling | "Test this freshness threshold" |
| `/armor:recommend` | AI-driven monitoring recommendations | "What should I monitor?" |

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

### Metrics
- `list_metrics(asset_id, metric_type, limit)` - List metrics for an asset
- `get_metrics_summary(asset_id)` - Get metrics summary
- `create_metric(asset_id, metric_type, table_path, column_name, capture_interval)` - Create metric
- `delete_metric(asset_id, metric_id)` - Delete metric
- `capture_metric(asset_id, metric_id)` - Trigger immediate capture

### Validity
- `list_validity_rules(asset_id, rule_type, limit)` - List validity rules
- `get_validity_summary(asset_id)` - Get validity summary
- `create_validity_rule(asset_id, rule_type, table_path, column_name, severity)` - Create rule
- `delete_validity_rule(asset_id, rule_id)` - Delete rule
- `check_validity_rule(asset_id, rule_id)` - Run check immediately

### Tags
- `list_tags(asset, category, limit)` - List tags for an asset
- `create_tag(asset, name, object_path, object_type, category, description)` - Create tag
- `apply_tags(asset, tag_names, object_paths, category)` - Apply tags to objects
- `bulk_apply_tag(tag_name, asset_ids, category)` - Apply tag to multiple assets

### Coverage
- `get_coverage_summary()` - Get monitoring coverage across all assets

### Dry-Run / Preview (TECH-771)
- `dry_run_freshness(asset_id, table_path, expected_interval_hours, lookback_days)` - Test freshness threshold
- `dry_run_schema(asset_id, table_path, lookback_days)` - Preview schema drift detection
- `preview_alerts(rule_id, event_types, severities, lookback_days)` - Preview alert rule matches
- `dry_run_metric(asset_id, table_path, metric_type, column_name, sensitivity, lookback_days)` - Test metric threshold

### Recommendations (TECH-772)
- `recommend_freshness(asset_id, min_confidence, limit, include_monitored)` - Suggest freshness schedules
- `recommend_metrics(asset_id, table_path, min_confidence, limit)` - Suggest quality metrics
- `get_coverage_recommendations(asset_id, limit)` - Identify monitoring gaps
- `recommend_thresholds(asset_id, days, limit)` - Suggest threshold adjustments

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
