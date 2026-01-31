---
name: armor-connect
description: Connect a new data source to AnomalyArmor. Handles "connect my database", "add snowflake", "setup postgres", "connect warehouse".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Connect Data Source

Guide users through connecting a new data source (database, warehouse) to AnomalyArmor.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)
- Database credentials ready

## When to Use

- "Connect my Snowflake warehouse"
- "Add my PostgreSQL database"
- "Setup Databricks connection"
- "Connect a new data source"

## Supported Data Sources

- `snowflake` - Snowflake Data Cloud
- `postgresql` - PostgreSQL
- `databricks` - Databricks
- `bigquery` - Google BigQuery
- `redshift` - Amazon Redshift
- `mysql` - MySQL
- `clickhouse` - ClickHouse

## Steps

1. Ask user for data source type if not specified
2. Collect connection configuration (credentials, host, database, etc.)
3. Create the asset with `client.assets.create()`
4. Test the connection with `client.assets.test_connection()`
5. If successful, trigger schema discovery with `client.assets.trigger_discovery()`
6. Track discovery progress with `client.jobs.status()`

## Example Usage

### Connect Snowflake

```python
from anomalyarmor import Client
import time

client = Client()

# Create the asset
asset = client.assets.create(
    name="Analytics Warehouse",
    source_type="snowflake",
    connection_config={
        "account": "abc123.us-east-1",
        "warehouse": "COMPUTE_WH",
        "database": "ANALYTICS",
        "user": "anomalyarmor_user",
        "password": "your_password",  # Or use key pair auth
        "role": "ANOMALYARMOR_ROLE"  # Optional
    },
    description="Main analytics data warehouse"
)
print(f"Created asset: {asset.id}")

# Test connection
result = client.assets.test_connection(asset.id)
if result.success:
    print("Connection successful!")
else:
    print(f"Connection failed: {result.error_message}")
    exit(1)

# Trigger schema discovery
job = client.assets.trigger_discovery(asset.id)
print(f"Discovery started: {job.job_id}")

# Wait for discovery to complete
while True:
    status = client.jobs.status(job.job_id)
    print(f"Discovery progress: {status.get('progress', 0)}%")
    if status.get('status') in ('completed', 'failed'):
        break
    time.sleep(5)

if status.get('status') == 'completed':
    print("Schema discovery complete!")
else:
    print(f"Discovery failed: {status.get('error')}")
```

### Connect PostgreSQL

```python
from anomalyarmor import Client

client = Client()

asset = client.assets.create(
    name="Production Database",
    source_type="postgresql",
    connection_config={
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "user": "readonly_user",
        "password": "your_password",
        "sslmode": "require"
    }
)

# Test and discover...
```

### Connect Databricks

```python
from anomalyarmor import Client

client = Client()

asset = client.assets.create(
    name="Databricks Lakehouse",
    source_type="databricks",
    connection_config={
        "host": "adb-1234567890.1.azuredatabricks.net",
        "http_path": "/sql/1.0/warehouses/abc123",
        "access_token": "dapi..."
    }
)
```

## Connection Config by Source Type

### Snowflake
```python
{
    "account": "abc123.us-east-1",
    "warehouse": "COMPUTE_WH",
    "database": "ANALYTICS",
    "user": "user",
    "password": "password",
    "role": "ROLE_NAME"  # optional
}
```

### PostgreSQL
```python
{
    "host": "hostname",
    "port": 5432,
    "database": "dbname",
    "user": "user",
    "password": "password",
    "sslmode": "require"  # optional
}
```

### BigQuery
```python
{
    "project_id": "my-project",
    "credentials_json": "{...}"  # Service account JSON
}
```

## Security Notes

- Never hardcode credentials in scripts
- Use environment variables or secure vaults
- Create read-only database users for AnomalyArmor
- Ensure network connectivity (whitelist IPs if needed)

## Follow-up Actions

After connecting, use:
- `/armor:monitor` to set up freshness and schema monitoring
- `/armor:analyze` to generate AI intelligence
- `/armor:status` to verify health
