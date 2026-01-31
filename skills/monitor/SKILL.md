---
name: armor-monitor
description: Set up monitoring for freshness and schema drift. Handles "monitor my table", "setup freshness", "enable schema monitoring", "track changes".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Set Up Monitoring

Configure freshness monitoring and schema drift detection for your data assets.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)
- Data source already connected (use `/armor:connect` first)

## When to Use

- "Set up freshness monitoring for the orders table"
- "Monitor my critical tables"
- "Enable schema drift detection"
- "Alert me when data is stale"
- "Track schema changes"

## Steps

### For Freshness Monitoring
1. Identify the asset and table to monitor
2. Determine check interval (how often to check)
3. Choose monitoring mode (auto_learn or explicit threshold)
4. Create schedule with `client.freshness.create_schedule()`

### For Schema Monitoring
1. Identify the asset to monitor
2. Create baseline with `client.schema.create_baseline()`
3. Enable monitoring with `client.schema.enable_monitoring()`

## Example Usage

### Set Up Freshness Monitoring (Auto-Learn)

```python
from anomalyarmor import Client

client = Client()

# List existing schedules for the asset
schedules = client.freshness.list_schedules(asset_id="asset-uuid")
print(f"Existing schedules: {len(schedules)}")

# Create freshness schedule with auto-learn
# System will learn normal update patterns and alert on deviations
schedule = client.freshness.create_schedule(
    asset_id="asset-uuid",
    table_path="public.orders",
    check_interval="1h",  # Check every hour
    monitoring_mode="auto_learn"
)

print(f"Created schedule: {schedule.id}")
print(f"Table: {schedule.table_path}")
print(f"Check interval: {schedule.check_interval}")
```

### Set Up Freshness with Explicit Threshold

```python
from anomalyarmor import Client

client = Client()

# Create schedule with explicit threshold
# Alert if table hasn't updated in 24 hours
schedule = client.freshness.create_schedule(
    asset_id="asset-uuid",
    table_path="public.daily_summary",
    check_interval="6h",
    monitoring_mode="explicit",
    expected_interval_hours=24,
    freshness_column="updated_at"  # Optional: specify column
)

print(f"Created schedule with {schedule.expected_interval_hours}h threshold")
```

### Enable Schema Drift Monitoring

```python
from anomalyarmor import Client

client = Client()

# Create schema baseline (captures current schema)
baseline = client.schema.create_baseline(
    asset_id="asset-uuid",
    description="Initial production baseline"
)
print(f"Baseline captured: {baseline.column_count} columns")

# Enable monitoring with daily checks
config = client.schema.enable_monitoring(
    asset_id="asset-uuid",
    schedule_type="daily",  # hourly, every_4_hours, daily, weekly
    auto_create_baseline=True  # Create baseline if none exists
)
print(f"Monitoring enabled, next check: {config.next_check_at}")
```

### Disable Monitoring

```python
from anomalyarmor import Client

client = Client()

# Delete freshness schedule
client.freshness.delete_schedule("schedule-uuid")

# Disable schema monitoring (keeps baseline)
client.schema.disable_monitoring("asset-uuid")
```

## Check Interval Options

| Interval | Description | Best For |
|----------|-------------|----------|
| `5m` | Every 5 minutes | Real-time data |
| `1h` | Hourly | Frequently updated tables |
| `6h` | Every 6 hours | Moderate update frequency |
| `1d` | Daily | Daily batch jobs |
| `1w` | Weekly | Weekly reports |

## Schedule Type Options (Schema)

| Type | Description |
|------|-------------|
| `hourly` | Check every hour |
| `every_4_hours` | Check every 4 hours |
| `daily` | Check once per day |
| `weekly` | Check once per week |

## Monitoring Mode

- **auto_learn** (recommended): System learns normal update patterns and alerts on deviations
- **explicit**: You specify expected update interval; alerts if exceeded

## Follow-up Actions

- Use `/armor:status` to verify monitoring is working
- Use `/armor:alerts` to see triggered alerts
- Adjust thresholds based on false positives/negatives
