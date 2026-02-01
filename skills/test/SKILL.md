---
name: armor-test
description: Test and preview monitoring configurations before enabling. Handles "dry-run threshold", "preview alerts", "test this rule", "what would fire".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Test Before Deploying

Preview what alerts would fire with proposed configurations. Avoid alert fatigue by testing thresholds before enabling.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Test this freshness threshold before I enable it"
- "What alerts would fire if I set the threshold to 4 hours?"
- "Dry-run the schema drift check"
- "Preview the impact of this rule"
- "Will this configuration cause too many alerts?"

## Steps

### Dry-Run Freshness Threshold
1. Specify the table and proposed threshold
2. Call `client.freshness.dry_run()` with proposed config
3. Review predicted alerts over historical data
4. Adjust threshold if too many/few alerts predicted
5. When satisfied, create the actual schedule

### Preview Alert Rules
1. Specify the event types to filter
2. Call `client.alerts.preview()` with event types
3. See what historical events would have triggered alerts
4. Evaluate alert frequency
5. Adjust configuration as needed

## Example Usage

### Dry-Run Freshness Threshold

```python
from anomalyarmor import Client

client = Client()

# Test what would happen with a 4-hour freshness threshold
# Uses historical data to predict alert frequency
result = client.freshness.dry_run(
    asset_id="asset-uuid",
    table_path="public.orders",
    expected_interval_hours=4,
    lookback_days=7
)

print(f"Configuration: Alert if stale for {result.threshold_hours} hours")
print(f"Historical period: {result.lookback_days} days")
print()
print(f"Total checks analyzed: {result.total_checks}")
print(f"Would alert count: {result.would_alert_count}")
print(f"Alert rate: {result.alert_rate_percent:.1f}%")
print()

if result.would_alert_now:
    print(f"Current status: Would alert NOW (age: {result.current_age_hours:.1f}h)")
else:
    print(f"Current status: OK (age: {result.current_age_hours:.1f}h)")

print(f"\nRecommendation: {result.recommendation}")
```

### Dry-Run Schema Drift Settings

```python
from anomalyarmor import Client

client = Client()

# Preview schema drift detection with proposed settings
result = client.schema.dry_run(
    asset_id="asset-uuid",
    lookback_days=30
)

print(f"Schema Drift Dry-Run Results:")
print(f"  Total changes detected: {result.total_changes}")
print(f"  Critical changes: {result.critical_changes}")
print(f"  Warning changes: {result.warning_changes}")
print(f"  Info changes: {result.info_changes}")
print()

if result.sample_changes:
    print("Sample changes:")
    for change in result.sample_changes[:5]:
        print(f"  - {change.change_type}: {change.object_name}")
```

### Preview Alert Rule Matches

```python
from anomalyarmor import Client

client = Client()

# Preview what alerts would match a rule configuration
result = client.alerts.preview(
    event_types=["freshness_stale", "schema_drift"],
    severities=["critical", "warning"],
    lookback_days=7
)

print(f"Lookback: {result.lookback_days} days")
print(f"Total alerts matched: {result.total_matched}")
print(f"Would send: {result.would_send_count}")
print(f"Alert rate: {result.alert_rate_per_day:.1f}/day")
print()

if result.sample_alerts:
    print("Sample alerts:")
    for alert in result.sample_alerts[:5]:
        print(f"  - {alert.timestamp}: {alert.event_type}")
```

### Dry-Run Metrics Threshold

```python
from anomalyarmor import Client

client = Client()

# Preview what anomalies would be detected with a metric
result = client.metrics.dry_run(
    asset_id="asset-uuid",
    table_path="catalog.schema.orders",
    metric_type="null_percent",
    column_name="email",
    sensitivity=1.5,
    lookback_days=14,
)

print(f"Metric Dry-Run: {result.metric_type} on {result.column_name}")
print(f"Total snapshots analyzed: {result.total_snapshots}")
print(f"Anomalies detected: {result.anomaly_count}")
print(f"Anomaly rate: {result.anomaly_rate_percent:.1f}%")
print()
print(f"Recommendation: {result.recommendation}")
```

## Interpreting Results

| Metric | Good Range | Action if Outside |
|--------|-----------|-------------------|
| Alert rate | 5-25% | Adjust threshold up/down |
| Alerts per day | 0.1 - 1.0 | Adjust threshold up/down |
| Zero alerts | - | Tighten threshold |

## Follow-up Actions

- If results look good: Use `/armor:monitor` to enable the configuration
- If too many alerts: Increase threshold or add conditions
- If no alerts: Decrease threshold to catch real issues
- Compare different configurations to find optimal settings
