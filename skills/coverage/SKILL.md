---
name: armor-coverage
description: Analyze monitoring coverage and gaps. Handles "what am I monitoring", "what tables have no alerts", "coverage gaps", "monitoring status", "unmonitored tables".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Monitoring Coverage

Analyze what's being monitored and identify gaps in your data observability coverage.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "What am I monitoring?"
- "What tables have no alerts?"
- "Show monitoring gaps"
- "Which tables need freshness checks?"
- "Coverage analysis"
- "Unmonitored critical tables"

## Coverage Categories

### Freshness Monitoring
- Tables with freshness schedules vs unmonitored
- SLA configurations

### Schema Monitoring
- Tables with schema baselines
- Drift detection status

### Data Quality
- Tables with metrics configured
- Validity rules coverage

### Alerting
- Tables with alert rules
- Notification coverage

## Steps

1. Get list of all assets
2. Check freshness schedules
3. Check metrics coverage
4. Check validity rules
5. Compare to identify gaps

## Example Usage

### Get Coverage Overview

```python
from anomalyarmor import Client

client = Client()

# Get all assets
assets = client.assets.list(limit=100)
total_assets = len(assets)

# Get freshness schedules
schedules = client.freshness.list_schedules(limit=100)
freshness_covered = len(set(s.asset_id for s in schedules))

# Get health summary
health = client.health.summary()

print(f"=== MONITORING COVERAGE ===")
print(f"\nTotal Assets: {total_assets}")
print(f"Freshness Monitored: {freshness_covered} ({100*freshness_covered//total_assets}%)")
print(f"\nHealth Status: {health.overall_status.upper()}")
```

### Find Unmonitored Tables

```python
# Get all asset IDs
all_asset_ids = {a.id for a in assets}

# Get monitored asset IDs from freshness
monitored_ids = {s.asset_id for s in schedules}

# Find gaps
unmonitored = all_asset_ids - monitored_ids

print(f"\nUnmonitored Tables ({len(unmonitored)}):")
for asset in assets:
    if asset.id in unmonitored:
        print(f"  {asset.qualified_name}")
```

### Check Per-Asset Coverage

```python
# Check coverage for a specific asset
asset_id = "asset-uuid"

# Freshness
try:
    freshness = client.freshness.status(asset_id)
    has_freshness = True
except Exception:
    has_freshness = False

# Metrics
metrics = client.metrics.list(asset_id)
has_metrics = len(metrics) > 0

# Validity
rules = client.validity.list(asset_id)
has_validity = len(rules) > 0

# Schema
try:
    schema = client.schema.baseline(asset_id)
    has_schema = True
except Exception:
    has_schema = False

print(f"Coverage for {asset_id}:")
print(f"  Freshness: {'✓' if has_freshness else '✗'}")
print(f"  Schema: {'✓' if has_schema else '✗'}")
print(f"  Metrics: {'✓' if has_metrics else '✗'} ({len(metrics)} metrics)")
print(f"  Validity: {'✓' if has_validity else '✗'} ({len(rules)} rules)")
```

### Prioritize Coverage Gaps

```python
# Find critical tables without monitoring
critical_assets = [a for a in assets if 'production' in a.qualified_name.lower()]

print("\nCritical Tables Needing Attention:")
for asset in critical_assets:
    metrics = client.metrics.list(asset.id)
    rules = client.validity.list(asset.id)

    if len(metrics) == 0 and len(rules) == 0:
        print(f"  {asset.qualified_name}")
        print(f"    NO MONITORING - Consider adding freshness + quality checks")
```

### Generate Coverage Report

```python
coverage_report = {
    "total_assets": total_assets,
    "freshness_coverage": {
        "monitored": freshness_covered,
        "percentage": 100 * freshness_covered // total_assets
    },
    "needs_attention": []
}

for asset in assets:
    metrics = client.metrics.list(asset.id)
    if len(metrics) == 0:
        coverage_report["needs_attention"].append({
            "asset": asset.qualified_name,
            "missing": "data quality metrics"
        })

print(f"Coverage Report: {coverage_report}")
```

## Expected Output

```
=== MONITORING COVERAGE ===

Total Assets: 45
Freshness Monitored: 38 (84%)
Schema Monitored: 42 (93%)
Metrics Configured: 35 (78%)
Alert Rules: 28 (62%)

Health Status: WARNING

Coverage by Category:
  Production Tables: 100% covered
  Staging Tables: 75% covered
  Raw Tables: 50% covered

Unmonitored Tables (7):
  raw.events_backup
  staging.temp_orders
  staging.test_data
  archive.orders_2023
  archive.customers_2023
  sandbox.dev_table
  sandbox.analysis

Recommended Actions:
  1. Add freshness monitoring to raw.events_backup
  2. Review if archive tables need monitoring
  3. Consider excluding sandbox from coverage metrics
```

## Follow-up Actions

- For unmonitored critical tables: Use `/armor:monitor` to add freshness
- For missing metrics: Use `/armor:quality` to add data quality checks
- For low alert coverage: Use `/armor:alerts` to create rules
- For schema gaps: Set up baselines via dashboard
- To improve coverage: Focus on production-critical tables first
