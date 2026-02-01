---
name: armor-quality
description: Add data quality checks with metrics and validity rules. Handles "add null check", "create row count metric", "list metrics", "add uniqueness check", "data quality status".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Data Quality

Set up and manage data quality checks including metrics (row counts, null rates, distinct counts) and validity rules (null checks, uniqueness, custom expressions).

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Add a null check to the email column"
- "Create a row count metric for orders"
- "What metrics exist for this table?"
- "Add a uniqueness check on customer_id"
- "Show data quality status"
- "Set up a freshness metric"

## Concepts

### Metrics
Metrics track quantitative measurements over time:
- **row_count**: Number of rows in a table
- **null_rate**: Percentage of null values in a column
- **distinct_count**: Number of unique values
- **freshness**: Time since last update

### Validity Rules
Rules that validate data integrity:
- **NOT_NULL**: Column must not contain nulls
- **UNIQUE**: Column values must be unique
- **ACCEPTED_VALUES**: Column values must be in allowed list
- **REGEX**: Column values must match pattern
- **CUSTOM**: Custom SQL expression

## Steps

### Creating a Metric

1. Get the asset ID for the target table
2. Choose metric type (row_count, null_rate, distinct_count, etc.)
3. Call `client.metrics.create()` with appropriate parameters
4. Optionally trigger immediate capture with `client.metrics.capture()`

### Creating a Validity Rule

1. Get the asset ID for the target table
2. Choose rule type (NOT_NULL, UNIQUE, ACCEPTED_VALUES, etc.)
3. Call `client.validity.create()` with column and rule parameters
4. Optionally run immediate check with `client.validity.check()`

## Example Usage

### List Existing Metrics

```python
from anomalyarmor import Client

client = Client()

# Get metrics summary
summary = client.metrics.summary("asset-uuid")
print(f"Total metrics: {summary.total_metrics}")
print(f"Failing metrics: {summary.failing_count}")

# List all metrics
metrics = client.metrics.list("asset-uuid")
for m in metrics:
    print(f"  {m.metric_type}: {m.name} ({m.status})")
```

### Create a Row Count Metric

```python
metric = client.metrics.create(
    asset_id="asset-uuid",
    metric_type="row_count",
    table_path="public.orders",
    capture_interval="daily",
)
print(f"Created metric: {metric.id}")
```

### Create a Null Check Rule

```python
rule = client.validity.create(
    asset_id="asset-uuid",
    rule_type="NOT_NULL",
    table_path="public.customers",
    column_name="email",
    severity="warning",
)
print(f"Created rule: {rule.id}")

# Run immediately
result = client.validity.check("asset-uuid", rule.id)
print(f"Check result: {result.status}")
```

### Create a Uniqueness Check

```python
rule = client.validity.create(
    asset_id="asset-uuid",
    rule_type="UNIQUE",
    table_path="public.orders",
    column_name="order_id",
    severity="critical",
)
```

## Expected Output

```
Metrics Summary for warehouse.public.orders:
  Total metrics: 3
  Passing: 2
  Failing: 1

Metrics:
  row_count: Daily Row Count (passing)
  null_rate: Email Null Rate (passing)
  distinct_count: Customer Distinct Count (failing)

Validity Rules:
  NOT_NULL: email_not_null (passing)
  UNIQUE: order_id_unique (passing)
```

## Follow-up Actions

- For failing metrics: Investigate the trend and set up alerts
- For failing validity rules: Review the data and fix source issues
- To monitor changes: Use `/armor:alerts` to create alert rules
- To understand impact: Use `/armor:lineage` to trace dependencies
