---
name: armor-profile
description: Profile tables and columns for statistics and distributions. Handles "profile this table", "show column stats", "data distribution", "table statistics", "cardinality analysis".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Data Profiling

Analyze table and column statistics, distributions, and data characteristics.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Profile this table"
- "Show column statistics"
- "What's the data distribution?"
- "Cardinality analysis"
- "Show null rates"
- "Table row counts over time"

## Profiling Metrics

### Table-Level Metrics
- **row_count**: Number of rows
- **freshness**: Time since last update

### Column-Level Metrics
- **null_rate**: Percentage of null values
- **distinct_count**: Number of unique values (cardinality)
- **min/max**: Value ranges for numeric/date columns

## Steps

1. Get metrics summary for the asset
2. List existing metrics to see what's being tracked
3. View metric snapshots for trends over time
4. Create new metrics if needed for additional coverage

## Example Usage

### Get Table Profile Summary

```python
from anomalyarmor import Client

client = Client()

# Get metrics summary
summary = client.metrics.summary("asset-uuid")
print(f"Total Metrics: {summary.total_metrics}")
print(f"Passing: {summary.passing_count}")
print(f"Failing: {summary.failing_count}")

# List all metrics
metrics = client.metrics.list("asset-uuid")
print("\nMetrics:")
for m in metrics:
    print(f"  {m.metric_type}: {m.name}")
    print(f"    Status: {m.status}")
    if m.last_value is not None:
        print(f"    Last Value: {m.last_value}")
```

### Get Column Statistics

```python
# List column-level metrics
column_metrics = client.metrics.list("asset-uuid", metric_type="null_rate")
print("Null Rates by Column:")
for m in column_metrics:
    print(f"  {m.column_name}: {m.last_value}%")

# Get distinct counts
distinct_metrics = client.metrics.list("asset-uuid", metric_type="distinct_count")
print("\nDistinct Counts:")
for m in distinct_metrics:
    print(f"  {m.column_name}: {m.last_value} unique values")
```

### View Trends Over Time

```python
# Get metric snapshots (historical values)
snapshots = client.metrics.snapshots(
    asset_id="asset-uuid",
    metric_id="metric-uuid",
    limit=30
)

print("Row Count Trend (last 30 days):")
for snapshot in snapshots:
    print(f"  {snapshot.captured_at}: {snapshot.value}")
```

### Create New Profile Metrics

```python
# Add row count metric
row_metric = client.metrics.create(
    asset_id="asset-uuid",
    metric_type="row_count",
    table_path="public.orders",
    capture_interval="daily"
)
print(f"Created row count metric: {row_metric.id}")

# Add null rate metric for a column
null_metric = client.metrics.create(
    asset_id="asset-uuid",
    metric_type="null_rate",
    table_path="public.orders",
    column_name="customer_id",
    capture_interval="daily"
)
print(f"Created null rate metric: {null_metric.id}")

# Add distinct count metric
distinct_metric = client.metrics.create(
    asset_id="asset-uuid",
    metric_type="distinct_count",
    table_path="public.orders",
    column_name="status",
    capture_interval="daily"
)
print(f"Created distinct count metric: {distinct_metric.id}")
```

### Trigger Immediate Capture

```python
# Capture metrics now (don't wait for schedule)
result = client.metrics.capture("asset-uuid", "metric-uuid")
print(f"Captured value: {result['value']}")
print(f"Captured at: {result['captured_at']}")
```

## Expected Output

```
=== Table Profile: warehouse.public.orders ===

Summary:
  Total Metrics: 8
  Passing: 7
  Failing: 1

Table Metrics:
  row_count: 1,234,567 rows
  freshness: Updated 2 hours ago

Column Statistics:
  order_id:
    Null Rate: 0%
    Distinct Count: 1,234,567 (100% unique)

  customer_id:
    Null Rate: 0.1%
    Distinct Count: 45,678

  status:
    Null Rate: 0%
    Distinct Count: 5 (enum-like)

  created_at:
    Null Rate: 0%
    Min: 2023-01-01
    Max: 2026-01-31

Row Count Trend (7 days):
  Jan 25: 1,200,000
  Jan 26: 1,210,000
  Jan 27: 1,220,000
  Jan 28: 1,225,000
  Jan 29: 1,230,000
  Jan 30: 1,232,000
  Jan 31: 1,234,567
```

## Follow-up Actions

- For high null rates: Create validity rules with `/armor:quality`
- For unexpected cardinality: Investigate with `/armor:investigate`
- For row count anomalies: Set up alerts with `/armor:alerts`
- For trending issues: Add more granular metrics
- To understand data flow: Check lineage with `/armor:lineage`
