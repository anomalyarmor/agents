---
name: armor-investigate
description: Investigate data issues using lineage, intelligence, and history. Handles "why is this table stale", "what changed", "explain this alert", "root cause analysis", "debug this issue".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Investigate Data Issues

Perform root cause analysis on data issues by combining lineage, intelligence, and historical data.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Why is this table stale?"
- "What changed in the schema?"
- "Explain this alert"
- "Why did freshness fail?"
- "Root cause analysis"
- "Debug this data issue"
- "What happened to this pipeline?"

## Investigation Workflow

### 1. Gather Context
- Get current status of the affected asset
- Check recent alerts and their details
- Review freshness and schema status

### 2. Trace Dependencies
- Use lineage to find upstream tables
- Identify which upstream tables are also affected
- Check if issue originates upstream

### 3. Analyze Intelligence
- Ask AI-powered questions about the issue
- Get recommendations based on historical patterns
- Understand impact across the data pipeline

### 4. Review History
- Check when the issue started
- Look at pattern of failures
- Identify recurring issues

## Steps

1. Start with `client.health.summary()` to understand current state
2. For specific issues, use `client.freshness.status()` or `client.schema.baseline()`
3. Use `client.lineage.get()` to trace dependencies
4. Use `client.intelligence.ask()` for AI-powered analysis
5. Check `client.alerts.list()` for related alerts

## Example Usage

### Investigate Stale Table

```python
from anomalyarmor import Client

client = Client()

# 1. Check current freshness status
freshness = client.freshness.status("asset-uuid")
print(f"Status: {freshness.status}")
print(f"Last Update: {freshness.last_updated_at}")
print(f"Expected: {freshness.expected_at}")

# 2. Get upstream lineage
lineage = client.lineage.get("asset-uuid", direction="upstream", depth=2)
print(f"\nUpstream Dependencies ({len(lineage.upstream)} tables):")
for node in lineage.upstream:
    print(f"  {node.qualified_name}")

# 3. Check upstream freshness
for node in lineage.upstream:
    try:
        upstream_status = client.freshness.status(node.asset_id)
        if upstream_status.status == "stale":
            print(f"  WARNING: {node.qualified_name} is also stale!")
    except Exception:
        pass

# 4. Ask AI for analysis
response = client.intelligence.ask(
    question="Why is the orders table stale and what should I do?",
    asset_ids=["asset-uuid"]
)
print(f"\nAI Analysis: {response.answer}")
```

### Investigate Alert

```python
# Get alert details
alerts = client.alerts.list(
    asset_id="asset-uuid",
    status="triggered",
    limit=5
)

for alert in alerts:
    print(f"Alert: {alert.message}")
    print(f"  Severity: {alert.severity}")
    print(f"  Triggered: {alert.triggered_at}")
    print(f"  Asset: {alert.qualified_name}")

# Ask AI about the alert
response = client.intelligence.ask(
    question=f"Explain this alert and what caused it: {alerts[0].message}",
    asset_ids=["asset-uuid"]
)
print(f"\nAI Explanation: {response.answer}")
```

### Investigate Schema Change

```python
# Get schema baseline and changes
baseline = client.schema.baseline("asset-uuid")
print(f"Schema Status: {baseline.status}")

# Check for recent changes
if baseline.unacknowledged_changes:
    print("\nUnacknowledged Changes:")
    for change in baseline.unacknowledged_changes:
        print(f"  {change.change_type}: {change.column_name}")
        print(f"    Detected: {change.detected_at}")

# Get downstream impact
lineage = client.lineage.get("asset-uuid", direction="downstream", depth=2)
print(f"\nDownstream Impact ({len(lineage.downstream)} tables may be affected):")
for node in lineage.downstream:
    print(f"  {node.qualified_name}")
```

## Expected Output

```
Investigation: orders table is stale

Freshness Status:
  Status: STALE
  Last Update: 2026-01-30 06:00:00
  Expected: 2026-01-31 06:00:00
  Delay: 24 hours

Upstream Dependencies (3 tables):
  raw.events - FRESH
  staging.orders_raw - STALE (root cause)
  staging.customers - FRESH

Root Cause: staging.orders_raw has not updated since 2026-01-30

AI Analysis:
  The orders table is stale because its upstream dependency staging.orders_raw
  has not received new data in 24 hours. This appears to be related to the
  ETL job failure at 2026-01-30 05:45. Recommended action: Check the Airflow
  logs for the orders_etl DAG.

Related Alerts:
  [CRITICAL] Freshness SLA breach - orders
  [WARNING] ETL job failed - staging.orders_raw
```

## Follow-up Actions

- After finding root cause: Fix the source issue
- For upstream issues: Use `/armor:lineage` to trace further
- For recurring issues: Set up better alerting with `/armor:alerts`
- For schema issues: Review and acknowledge changes in dashboard
- To monitor fix: Use `/armor:status` to verify resolution
