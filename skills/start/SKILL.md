---
name: armor-start
description: Guided onboarding for new users. Handles "get started", "help me set up", "new to anomalyarmor", "first time setup", "onboarding".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Get Started with AnomalyArmor

A guided onboarding experience to set up data observability for your data assets.

## Prerequisites

- AnomalyArmor account (sign up at anomalyarmor.ai)
- API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Get me started with AnomalyArmor"
- "Help me set up data monitoring"
- "I'm new to AnomalyArmor"
- "First time setup"
- "Walk me through onboarding"

## Onboarding Steps

### Step 1: Verify Authentication

```python
from anomalyarmor import Client

# This will fail if not configured
client = Client()
print("Authentication successful!")
```

### Step 2: Connect Your First Data Source

See `/armor:connect` for detailed instructions.

```python
from anomalyarmor import Client

client = Client()

# Example: Connect PostgreSQL
asset = client.assets.create(
    name="My Database",
    source_type="postgresql",
    connection_config={
        "host": "your-host.com",
        "port": 5432,
        "database": "your_db",
        "user": "readonly_user",
        "password": "your_password"
    }
)

# Test connection
result = client.assets.test_connection(asset.id)
if result.success:
    print("Connected successfully!")

    # Trigger schema discovery
    job = client.assets.trigger_discovery(asset.id)
    print(f"Schema discovery started: {job.job_id}")
else:
    print(f"Connection failed: {result.error_message}")
```

### Step 3: Set Up Freshness Monitoring

See `/armor:monitor` for detailed instructions.

```python
from anomalyarmor import Client

client = Client()

# Monitor your most critical table
schedule = client.freshness.create_schedule(
    asset_id="your-asset-uuid",
    table_path="public.orders",  # Your critical table
    check_interval="1h",
    monitoring_mode="auto_learn"
)

print(f"Freshness monitoring enabled for {schedule.table_path}")
```

### Step 4: Enable Schema Drift Detection

```python
from anomalyarmor import Client

client = Client()

# Enable schema monitoring
config = client.schema.enable_monitoring(
    asset_id="your-asset-uuid",
    schedule_type="daily",
    auto_create_baseline=True
)

print(f"Schema monitoring enabled, next check: {config.next_check_at}")
```

### Step 5: Generate Intelligence

See `/armor:analyze` for detailed instructions.

```python
from anomalyarmor import Client

client = Client()

# Generate AI-powered intelligence
result = client.intelligence.generate(asset="your-asset-uuid")
print(f"Intelligence generation started: {result.job_id}")
print("This may take a few minutes...")
```

### Step 6: Verify Everything is Working

See `/armor:status` for detailed instructions.

```python
from anomalyarmor import Client

client = Client()

# Check overall health
health = client.health.summary()
print(f"Status: {health.overall_status}")

if health.overall_status == "healthy":
    print("Congratulations! Your data observability is set up.")
else:
    print("Some items need attention:")
    for item in health.needs_attention:
        print(f"  - {item.title}")
```

## Quick Start Checklist

- [ ] API key configured
- [ ] Data source connected
- [ ] Connection tested successfully
- [ ] Schema discovery completed
- [ ] Freshness monitoring enabled
- [ ] Schema drift detection enabled
- [ ] Intelligence generated
- [ ] Health check shows "healthy"

## Available Skills

After setup, you can use these skills:

| Skill | Description |
|-------|-------------|
| `/armor:status` | Check overall data health |
| `/armor:alerts` | View and manage alerts |
| `/armor:connect` | Connect additional data sources |
| `/armor:monitor` | Configure monitoring |
| `/armor:ask` | Ask questions about your data |
| `/armor:analyze` | Generate AI intelligence |

## Need Help?

- Documentation: docs.anomalyarmor.ai
- Support: support@anomalyarmor.ai
- Dashboard: app.anomalyarmor.ai

## Common Issues

### "No API key configured"
Set `ARMOR_API_KEY` environment variable or create `~/.armor/config.yaml`:
```yaml
api_key: aa_live_your_key_here
```

### "Connection failed"
- Verify credentials are correct
- Check network connectivity
- Ensure database user has required permissions
- Check if IP whitelisting is needed

### "Intelligence not available"
Run `/armor:analyze` first to generate intelligence.
