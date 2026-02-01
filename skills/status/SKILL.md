---
name: armor-status
description: Check data health, alerts, freshness issues, schema changes. Handles "is my data healthy", "any issues", "what's broken", "status check", "health summary".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Status Check

Check overall data health across all your monitored assets. This skill provides a quick summary of alerts, freshness issues, and schema changes.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Is my data healthy?"
- "Any issues I should know about?"
- "What's the status of my data?"
- "Give me a health summary"
- "What's broken?"

## Steps

1. Call `client.health.summary()` to get aggregated health status
2. Present the `overall_status` (healthy/warning/critical)
3. Show counts from component summaries (alerts, freshness, schema_drift)
4. List items from `needs_attention` with severity ranking
5. For critical issues, suggest next steps

## Example Usage

```python
from anomalyarmor import Client

client = Client()

# Get unified health summary
health = client.health.summary()

print(f"Overall Status: {health.overall_status.upper()}")
print()

# Show component summaries
print("Component Status:")
print(f"  Alerts: {health.alerts.unresolved_alerts} unresolved")
print(f"  Freshness: {health.freshness.stale_count} stale tables")
print(f"  Schema: {health.schema_drift.unacknowledged} unacknowledged changes")
print()

# Show items needing attention
if health.needs_attention:
    print("Items Needing Attention:")
    for item in health.needs_attention:
        print(f"  [{item.severity.upper()}] {item.title}")
        if item.asset_name:
            print(f"    Asset: {item.asset_name}")
else:
    print("No issues requiring attention.")
```

## Expected Output

```
Overall Status: WARNING

Component Status:
  Alerts: 3 unresolved
  Freshness: 2 stale tables
  Schema: 1 unacknowledged changes

Items Needing Attention:
  [CRITICAL] orders table stale for 6 hours
    Asset: orders
  [WARNING] Schema change detected in users table
    Asset: users
  [INFO] New alert rule triggered
    Asset: customers
```

## Follow-up Actions

Based on status, suggest:
- For stale tables: Use `/armor:monitor` to adjust schedules
- For unresolved alerts: Use `/armor:alerts` to investigate
- For schema changes: Review changes in AnomalyArmor dashboard
- For healthy status: No action needed
