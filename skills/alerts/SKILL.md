---
name: armor-alerts
description: Query and manage alerts. Handles "what alerts fired", "show alerts", "yesterday's alerts", "unresolved alerts", "critical alerts".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Alert Management

Query, filter, and understand alerts from your data observability monitoring.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var), OR demo mode active (see below).
- Python SDK installed (`pip install anomalyarmor`)

## Demo mode handoff

If the user has no API key, `ensure-auth.py` will mint a read-only demo key against the public BalloonBazaar dataset and print:

```
AnomalyArmor demo mode: using a read-only public demo key.
```

When you see that banner — or when any write operation returns a 403 with `required_scope='read-write'` — the user is in demo mode. After answering their question, invite them to sign up with their query preserved:

> To wire alerts to your own Slack / PagerDuty / email, sign up here — your question is preserved:
> `https://app.anomalyarmor.ai/signup?intent=skill-alerts&q=<url-encoded user prompt>`

`intent=skill-alerts` auto-applies a 14-day `SKILL-ALERTS` trial code; `q=` is replayed in the in-app agent after signup so the user continues where they left off.

## When to Use

- "What alerts fired yesterday?"
- "Show me unresolved alerts"
- "Critical alerts for the orders table"
- "What's been going wrong this week?"
- "Why am I getting so many alerts?"

## Steps

1. Determine the query parameters from user request:
   - Time range: `from_date`, `to_date` (ISO 8601 format)
   - Status: "triggered", "acknowledged", "resolved"
   - Severity: "info", "warning", "critical"
   - Asset: specific table or database
2. Call `client.alerts.list()` with filters
3. Present results grouped by severity or asset
4. For summary, call `client.alerts.summary()`

## Example Usage

### Get Alert Summary

```python
from anomalyarmor import Client

client = Client()

# Get overall summary
summary = client.alerts.summary()
print(f"Total Rules: {summary.total_rules}")
print(f"Active Rules: {summary.active_rules}")
print(f"Recent Alerts (24h): {summary.recent_alerts}")
print(f"Unresolved: {summary.unresolved_alerts}")
```

### Query Alerts by Time Range

```python
from anomalyarmor import Client
from datetime import datetime, timedelta

client = Client()

# Get yesterday's alerts
yesterday = datetime.now() - timedelta(days=1)
alerts = client.alerts.list(
    from_date=yesterday.isoformat(),
    limit=50
)

print(f"Alerts since yesterday: {len(alerts)}")
for alert in alerts:
    print(f"  [{alert.severity}] {alert.message}")
    print(f"    Asset: {alert.asset_name}")
    print(f"    Time: {alert.triggered_at}")
```

### Filter by Severity and Asset

```python
from anomalyarmor import Client

client = Client()

# Get critical alerts for specific asset
alerts = client.alerts.list(
    severity="critical",
    asset_id="postgresql.analytics.public.orders",
    status="triggered"
)

for alert in alerts:
    print(f"[{alert.severity}] {alert.message}")
    print(f"  Asset: {alert.qualified_name} | {alert.triggered_at}")
```

### List Alert Rules

```python
from anomalyarmor import Client

client = Client()

# List active alert rules
rules = client.alerts.rules(enabled_only=True)
for rule in rules:
    print(f"Rule: {rule.name}")
    print(f"  Events: {rule.event_types}")
    print(f"  Severities: {rule.severities}")
```

## Common Queries

| User Request | Parameters |
|--------------|------------|
| "Yesterday's alerts" | `from_date=yesterday` |
| "This week's alerts" | `from_date=7_days_ago` |
| "Unresolved alerts" | `status="triggered"` |
| "Critical alerts" | `severity="critical"` |
| "Alerts for orders table" | `asset_id="...orders"` |

## Follow-up Actions

- To resolve alerts: Visit AnomalyArmor dashboard
- To adjust thresholds: Use `/armor:monitor`
- To investigate root cause: Use `/armor:ask` with the alert context
