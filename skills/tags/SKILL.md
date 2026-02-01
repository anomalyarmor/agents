---
name: armor-tags
description: Classify and govern data with tags. Handles "tag this table as PII", "apply financial tag", "list tags", "classify data", "add governance label".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Data Classification with Tags

Organize and classify database objects with tags for governance, compliance, and business categorization.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "Tag this table as PII"
- "Apply financial reporting tag"
- "List all tags for this asset"
- "Mark these columns as sensitive"
- "Classify this data as confidential"
- "Add governance labels"

## Concepts

### Tag Categories
- **business**: Business domain tags (e.g., "finance", "marketing", "sales")
- **technical**: Technical classification (e.g., "fact_table", "dimension", "staging")
- **governance**: Compliance and security (e.g., "pii", "confidential", "gdpr")

### Tag Scope
Tags can be applied to:
- **Tables**: Full table classification
- **Columns**: Column-level classification (for PII, sensitive data)

## Steps

### Creating a Tag

1. Identify the asset and object (table or column) to tag
2. Choose the tag name and category
3. Call `client.tags.create()` with the object path

### Applying Multiple Tags

1. Prepare list of tag names to apply
2. Prepare list of object paths
3. Call `client.tags.apply()` for batch operations

### Bulk Tagging Across Assets

1. Create tag name
2. List asset IDs to tag
3. Call `client.tags.bulk_apply()`

## Example Usage

### List Existing Tags

```python
from anomalyarmor import Client

client = Client()

# List all tags for an asset
tags = client.tags.list(asset="postgresql.analytics")
for tag in tags:
    print(f"  {tag.name} ({tag.category}): {tag.object_path}")

# Filter by category
governance_tags = client.tags.list(
    asset="postgresql.analytics",
    category="governance"
)
```

### Tag a Table as PII

```python
tag = client.tags.create(
    asset="postgresql.analytics",
    name="pii_data",
    object_path="public.customers",
    object_type="table",
    category="governance",
    description="Contains personally identifiable information"
)
print(f"Created tag: {tag.id}")
```

### Tag a Column as Sensitive

```python
tag = client.tags.create(
    asset="postgresql.analytics",
    name="sensitive",
    object_path="public.customers.email",
    object_type="column",
    category="governance"
)
```

### Apply Multiple Tags to Multiple Tables

```python
result = client.tags.apply(
    asset="postgresql.analytics",
    tag_names=["financial_reporting", "quarterly_data"],
    object_paths=["gold.fact_orders", "gold.fact_revenue", "gold.dim_customers"],
    category="business"
)
print(f"Applied: {result.applied}, Failed: {result.failed}")
```

### Tag Multiple Assets

```python
result = client.tags.bulk_apply(
    tag_name="production_critical",
    asset_ids=["postgresql.analytics", "postgresql.warehouse", "snowflake.main"],
    category="technical"
)
print(f"Tagged {result.applied} assets")
```

## Expected Output

```
Tags for postgresql.analytics:
  pii_data (governance): public.customers
  financial_reporting (business): gold.fact_orders
  quarterly_data (business): gold.fact_revenue
  production_critical (technical): asset-level

By Category:
  governance: 3 tags
  business: 5 tags
  technical: 2 tags
```

## Follow-up Actions

- After tagging PII: Set up access controls and audit logging
- After business classification: Use tags to filter dashboards and reports
- After technical tagging: Use tags to prioritize monitoring
- To view tagged data: Filter assets by tag in the AnomalyArmor dashboard
