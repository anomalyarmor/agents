---
name: armor-analyze
description: Trigger AI analysis for your data assets. Handles "analyze my database", "generate intelligence", "refresh analysis", "update AI knowledge".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Analyze Your Data

Trigger AI-powered analysis to generate intelligence, descriptions, and knowledge base for your data assets.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)
- Data source connected (use `/armor:connect` first)

## When to Use

- "Analyze my database"
- "Generate intelligence for the warehouse"
- "Refresh AI analysis after schema changes"
- "Update the knowledge base"
- After connecting a new data source
- After major schema changes

## What Intelligence Includes

- Table and column descriptions
- Data type analysis
- Relationship detection
- Business context inference
- Knowledge base for Q&A (`/armor:ask`)

## Steps

1. Identify the asset to analyze
2. Trigger analysis with `client.intelligence.generate()`
3. Track progress with `client.jobs.status()`
4. Use `/armor:ask` once complete

## Example Usage

### Generate Intelligence for Full Asset

```python
from anomalyarmor import Client
import time

client = Client()

# Trigger intelligence generation
result = client.intelligence.generate(
    asset="postgresql.analytics"
)

print(f"Job started: {result.job_id}")

# Poll for completion
while True:
    status = client.jobs.status(result.job_id)
    progress = status.get('progress', 0)
    state = status.get('status', 'unknown')

    print(f"Status: {state}, Progress: {progress}%")

    if state == 'completed':
        print("Intelligence generation complete!")
        break
    elif state == 'failed':
        print(f"Failed: {status.get('error')}")
        break

    time.sleep(10)  # Wait 10 seconds between checks
```

### Analyze Specific Schemas

```python
from anomalyarmor import Client

client = Client()

# Only analyze specific schemas
result = client.intelligence.generate(
    asset="postgresql.analytics",
    include_schemas="public,analytics"  # Comma-separated
)

print(f"Analyzing schemas: public, analytics")
print(f"Job ID: {result.job_id}")
```

### Force Refresh After Changes

```python
from anomalyarmor import Client

client = Client()

# Force regeneration even if intelligence exists
result = client.intelligence.generate(
    asset="postgresql.analytics",
    force_refresh=True
)

print(f"Forcing refresh: {result.job_id}")
```

### Check Job Status

```python
from anomalyarmor import Client

client = Client()

# Check status of any async job
status = client.jobs.status("job-uuid")

print(f"Job ID: {status.get('job_id')}")
print(f"Status: {status.get('status')}")  # pending, running, completed, failed
print(f"Progress: {status.get('progress')}%")
print(f"Workflow: {status.get('workflow_name')}")

if status.get('status') == 'failed':
    print(f"Error: {status.get('error')}")
```

## Job States

| State | Description |
|-------|-------------|
| `pending` | Job queued, waiting to start |
| `running` | Job in progress |
| `completed` | Job finished successfully |
| `failed` | Job encountered an error |

## Timing

- Small databases (< 100 tables): 1-2 minutes
- Medium databases (100-500 tables): 2-5 minutes
- Large databases (500+ tables): 5-15 minutes

## When to Regenerate

- After adding new tables or columns
- After significant schema changes
- After changing business context
- Periodically (monthly) to keep context fresh

## Follow-up Actions

- Use `/armor:ask` to query the generated intelligence
- Use `/armor:status` to check overall health
- Review generated descriptions in AnomalyArmor dashboard
