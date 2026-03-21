# AnomalyArmor Agents

AI skills and MCP server for AnomalyArmor data observability. Monitor data quality, detect schema drift, and manage alerts directly from Claude Code, Cursor, or any MCP-compatible AI tool.

**Version**: 0.6.0 | **Tools**: 29 consolidated MCP tools | **Skills**: 14 slash commands

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
- `/armor:recommend` - Get AI monitoring recommendations
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
| `/armor:start` | Guided onboarding for new users | "Help me get set up" |
| `/armor:status` | Health summary across all assets | "Is my data healthy?" |
| `/armor:connect` | Connect a new data source | "Connect my Snowflake warehouse" |
| `/armor:monitor` | Set up freshness and schema monitoring | "Monitor freshness for orders table" |
| `/armor:alerts` | Query and manage alerts | "What alerts fired yesterday?" |
| `/armor:ask` | Natural language Q&A about your data | "What tables contain customer data?" |
| `/armor:analyze` | Trigger AI analysis | "Analyze the finance schema" |
| `/armor:quality` | Data quality metrics and validity rules | "Add null check for customer_id" |
| `/armor:coverage` | Monitoring coverage analysis | "What tables have no monitoring?" |
| `/armor:recommend` | AI-driven monitoring recommendations | "What should I monitor?" |
| `/armor:tags` | Asset tagging and classification | "Tag this table as PII" |
| `/armor:investigate` | Root cause analysis | "Why is this table stale?" |
| `/armor:lineage` | Data lineage exploration | "What depends on this table?" |
| `/armor:profile` | Table profiling and stats | "Profile the orders table" |

## MCP Tools (29 consolidated)

Tools follow a consolidated pattern: one tool per domain handles multiple operations via an `action` parameter, reducing context window usage while maintaining full functionality.

### Health and Briefing
- `health_summary()` - Overall data health across all assets
- `get_todays_briefing()` - Daily AI briefing with alerts, freshness, and coverage gaps

### Alerts (5 tools)
- `get_alerts_summary()` - Alert counts by severity and status
- `list_alerts(status, severity, asset_id, from_date, to_date)` - Query alerts with filters
- `list_inbox_alerts(status, limit)` - Unresolved alerts inbox
- `update_alert(alert_id, action, ...)` - Acknowledge, resolve, snooze, or comment on alerts
- `get_alert_trends(period)` - Alert trends over time
- `get_alert_history(alert_id)` - Full history for a specific alert

### Alert Rules (3 tools)
- `list_alert_rules(asset_id, is_active)` - List configured rules
- `create_alert_rule(asset_id, rule_type, ...)` - Create new alert rule
- `manage_alert_rule(rule_id, action, ...)` - Update, delete, enable/disable, or duplicate rules

### Assets (3 tools)
- `list_assets(source, asset_type, search)` - List monitored assets
- `create_asset(name, source_type, connection_config)` - Create data source
- `manage_asset(asset_id, action, ...)` - Update, delete, test connection, or trigger discovery
- `trigger_asset_discovery(asset_id)` - Start schema discovery

### Freshness (4 tools)
- `get_freshness_summary()` - Freshness overview across all assets
- `check_freshness(asset_id, table_path)` - Check specific table freshness
- `setup_freshness(asset_id, table_path, check_interval, ...)` - Create freshness schedule
- `list_freshness_schedules(asset_id)` - List configured schedules
- `manage_freshness_schedule(schedule_id, action, ...)` - Update, delete, pause/resume schedules

### Schema Drift (5 tools)
- `get_schema_summary()` - Schema drift overview
- `list_schema_changes(asset_id, severity, from_date, to_date)` - List detected changes
- `create_schema_baseline(asset_id, description)` - Create baseline
- `enable_schema_monitoring(asset_id, schedule_type, notify_on)` - Enable monitoring
- `disable_schema_monitoring(asset_id)` - Disable monitoring
- `get_schema_monitoring(asset_id)` - View current monitoring config
- `dry_run_schema(asset_id, schedule_type)` - Test schema monitoring before enabling

### Data Quality (4 tools)
- `get_metrics_summary(asset_id)` / `list_metrics(asset_id)` - View metrics
- `create_metric(asset_id, metric_type, table_path, ...)` - Create row count, null rate, or custom metric
- `manage_metric(metric_id, action, ...)` - Update, delete, capture, or view snapshots
- `get_validity_summary(asset_id)` / `list_validity_rules(asset_id)` - View validity rules
- `create_validity_rule(asset_id, rule_type, table_path, ...)` - Create validity rule
- `manage_validity_rule(rule_id, action, ...)` - Update, delete, check, or view results

### Referential Integrity (2 tools)
- `create_referential_check(asset_id, ...)` - Create cross-table referential check
- `manage_referential(check_id, action, ...)` - List, delete, run, or view results

### Destinations (4 tools)
- `list_destinations(destination_type)` - List alert destinations (Slack, email, webhook)
- `setup_destination(destination_type, ...)` - Create Slack channel, email, or webhook destination
- `manage_destination(destination_id, action, ...)` - Update, delete, test, enable/disable
- `manage_rule_destinations(rule_id, action, ...)` - Link/unlink destinations to alert rules

### Coverage and Recommendations (3 tools)
- `get_coverage(asset_id)` - Coverage tier and score for an asset
- `manage_coverage(asset_id, action)` - Get next steps or apply recommended monitoring
- `recommend(asset_id, recommendation_type)` - AI recommendations for freshness, metrics, coverage, or thresholds

### Intelligence (2 tools)
- `ask_question(asset, question)` - Natural language Q&A
- `generate_intelligence(asset)` - Trigger AI knowledge base generation

### Catalog (4 tools)
- `get_lineage(asset_id, depth, direction)` - Data lineage graph
- `job_status(job_id)` - Check async job status
- `create_tag(asset_id, name, object_path, ...)` - Create and assign tags
- `list_tags(asset_id)` / `apply_tags(asset_id, ...)` - List and apply tags

### API Keys
- `get_api_key_info()` - View current API key details and permissions

## Examples

### Check Data Health

```
User: Is my data healthy?

Your data health status:
- Overall: WARNING
- 3 unresolved alerts (1 critical, 2 warning)
- 2 stale tables (orders, customers)
- 1 unacknowledged schema change
- Coverage: 65% (Tier 2: Protected)
```

### Get AI Recommendations

```
User: What should I monitor on my Snowflake warehouse?

Based on your table patterns and update frequency:
1. orders (high traffic) - Add freshness check (hourly), row count metric
2. customers (PII) - Enable schema drift monitoring, add null checks
3. payments (financial) - Add freshness + row count + validity rules

Want me to set these up? I can configure all three in one go.
```

### Daily Briefing

```
User: What happened overnight?

Your daily briefing:
- 2 new alerts: orders table stale (6h), schema change in users
- Coverage improved: finance schema now at Tier 3 (Verified)
- Recommendation: 4 tables still have no monitoring. Run /armor:recommend.
```

### Root Cause Analysis

```
User: Why is the orders table stale?

Investigation results:
- Last update: 6 hours ago (expected: hourly)
- Upstream dependency: raw_orders was last updated 8 hours ago
- Likely cause: upstream ETL job failed or delayed
- Impact: 3 downstream dashboards affected
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
