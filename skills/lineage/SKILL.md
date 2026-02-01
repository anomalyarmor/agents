---
name: armor-lineage
description: Explore data lineage and dependencies. Handles "what depends on this table", "where does this data come from", "impact analysis", "upstream dependencies", "downstream consumers".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Data Lineage

Explore upstream dependencies and downstream consumers of your data assets.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)

## When to Use

- "What depends on this table?"
- "Where does this data come from?"
- "Impact analysis for changes"
- "Show upstream dependencies"
- "List downstream consumers"
- "Trace data flow"

## Concepts

### Directions
- **upstream**: Tables that this table depends on (data sources)
- **downstream**: Tables that depend on this table (data consumers)
- **both**: Full lineage graph in both directions

### Depth
- **depth=1**: Direct dependencies only
- **depth=2**: Two levels of dependencies
- **depth=3+**: Extended dependency chain (max 5)

## Steps

1. Identify the asset to analyze
2. Determine direction (upstream, downstream, or both)
3. Choose appropriate depth (start with 1-2)
4. Call `client.lineage.get()` to fetch lineage graph
5. Analyze the graph for impact or root cause

## Example Usage

### Find Upstream Dependencies

```python
from anomalyarmor import Client

client = Client()

# Get upstream lineage (where data comes from)
lineage = client.lineage.get(
    asset_id="asset-uuid",
    direction="upstream",
    depth=2
)

print(f"Table: {lineage.root.qualified_name}")
print(f"\nUpstream Dependencies ({len(lineage.upstream)} tables):")
for node in lineage.upstream:
    print(f"  {node.qualified_name}")
    if node.asset_type:
        print(f"    Type: {node.asset_type}")
```

### Find Downstream Consumers

```python
# Get downstream lineage (what depends on this)
lineage = client.lineage.get(
    asset_id="asset-uuid",
    direction="downstream",
    depth=2
)

print(f"Table: {lineage.root.qualified_name}")
print(f"\nDownstream Consumers ({len(lineage.downstream)} tables):")
for node in lineage.downstream:
    print(f"  {node.qualified_name}")
```

### Impact Analysis

```python
# Full impact analysis before making changes
lineage = client.lineage.get(
    asset_id="asset-uuid",
    direction="both",
    depth=3
)

print("=== IMPACT ANALYSIS ===")
print(f"\nTable: {lineage.root.qualified_name}")

# Upstream (what feeds this table)
print(f"\nData Sources ({len(lineage.upstream)} tables):")
for node in lineage.upstream:
    print(f"  <- {node.qualified_name}")

# Downstream (what will be affected by changes)
print(f"\nWill Impact ({len(lineage.downstream)} tables):")
for node in lineage.downstream:
    print(f"  -> {node.qualified_name}")

# Edges show the relationships
print(f"\nRelationships ({len(lineage.edges)} edges):")
for edge in lineage.edges:
    print(f"  {edge.source} -> {edge.target}")
```

### List All Lineage

```python
# List lineage summaries for multiple assets
lineage_list = client.lineage.list(limit=50)
for item in lineage_list:
    print(f"{item.qualified_name}:")
    print(f"  Upstream: {item.upstream_count}")
    print(f"  Downstream: {item.downstream_count}")
```

## Expected Output

```
=== IMPACT ANALYSIS ===

Table: warehouse.gold.fact_orders

Data Sources (4 tables):
  <- warehouse.staging.orders_raw
  <- warehouse.staging.customers
  <- warehouse.staging.products
  <- warehouse.raw.events

Will Impact (7 tables):
  -> warehouse.gold.daily_revenue
  -> warehouse.gold.customer_metrics
  -> warehouse.reporting.exec_dashboard
  -> warehouse.reporting.sales_report
  -> warehouse.ml.churn_features
  -> warehouse.ml.ltv_predictions
  -> external.bi_tool.orders_view

Relationships (11 edges):
  staging.orders_raw -> gold.fact_orders
  staging.customers -> gold.fact_orders
  ...
```

## Follow-up Actions

- For upstream issues: Investigate source tables with `/armor:investigate`
- For impact analysis: Notify downstream consumers of planned changes
- For data quality: Set up monitoring with `/armor:quality` on critical paths
- For schema changes: Review lineage before applying changes
- To understand data flow: Export lineage to documentation
