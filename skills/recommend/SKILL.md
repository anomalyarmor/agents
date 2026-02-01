---
name: armor-recommend
description: Get AI-driven recommendations for what to monitor. Handles "what should I monitor", "suggest tables", "recommend thresholds", "coverage gaps".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Monitoring Recommendations

Get AI-driven recommendations for what to monitor and how to configure thresholds based on historical patterns.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)
- Data source connected with discovery completed

## When to Use

- "What should I monitor?"
- "Suggest tables to monitor"
- "What are good thresholds for this table?"
- "What's missing from my monitoring?"
- "Help me set up monitoring for my warehouse"
- "Which tables are most critical?"

## Steps

### Get Freshness Recommendations
1. Call `client.recommendations.freshness()` for asset
2. Review prioritized list of tables with suggested thresholds
3. For each table, see why it's recommended
4. Use `/armor:test` to dry-run before enabling
5. Use `/armor:monitor` to enable

### Get Metrics Recommendations
1. Specify the table to analyze (optional)
2. Call `client.recommendations.metrics()` with table details
3. Review suggested metrics based on column analysis
4. Create metrics with `/armor:quality`

### Analyze Coverage
1. Call `client.recommendations.coverage()` for asset
2. Review coverage percentage and gaps
3. Prioritize high-importance unmonitored tables
4. Use recommendations to fill gaps

## Example Usage

### Get Freshness Recommendations

```python
from anomalyarmor import Client

client = Client()

# Get recommendations for which tables need freshness monitoring
recommendations = client.recommendations.freshness(
    asset_id="asset-uuid",
    min_confidence=0.7,
    limit=10
)

print(f"Freshness Recommendations ({len(recommendations.recommendations)}):")
print()

for rec in recommendations.recommendations:
    print(f"Table: {rec.table_path}")
    print(f"  Suggested interval: {rec.suggested_check_interval}")
    print(f"  Suggested threshold: {rec.suggested_threshold_hours} hours")
    print(f"  Detected frequency: {rec.detected_frequency}")
    print(f"  Confidence: {rec.confidence:.0%}")
    print(f"  Reason: {rec.reasoning}")
    print(f"  Data points: {rec.data_points}")
    print()

print(f"\nSummary:")
print(f"  Tables analyzed: {recommendations.tables_analyzed}")
print(f"  Tables with recommendations: {recommendations.tables_with_recommendations}")
```

### Get Metrics Recommendations

```python
from anomalyarmor import Client

client = Client()

# Get recommended metrics for a specific table
recommendations = client.recommendations.metrics(
    asset_id="asset-uuid",
    table_path="public.orders"  # Optional: omit for all tables
)

print(f"Metrics Recommendations ({len(recommendations.recommendations)}):")
print()

for rec in recommendations.recommendations:
    print(f"Table: {rec.table_path}")
    print(f"  Column: {rec.column_name}")
    print(f"  Suggested metric: {rec.suggested_metric_type}")
    print(f"  Confidence: {rec.confidence:.0%}")
    print(f"  Reason: {rec.reasoning}")
    print()

print(f"\nSummary:")
print(f"  Columns analyzed: {recommendations.columns_analyzed}")
print(f"  Columns with recommendations: {recommendations.columns_with_recommendations}")
```

### Analyze Coverage Gaps

```python
from anomalyarmor import Client

client = Client()

# Analyze monitoring coverage
coverage = client.recommendations.coverage(
    asset_id="asset-uuid"
)

print(f"Monitoring Coverage Analysis")
print(f"=" * 40)
print()

print(f"Coverage: {coverage.coverage_percentage:.1f}%")
print(f"  Total tables: {coverage.total_tables}")
print(f"  Monitored: {coverage.monitored_tables}")
print()

if coverage.recommendations:
    print("High-Priority Gaps:")
    for rec in coverage.recommendations[:5]:
        print(f"  - {rec.table_path}")
        print(f"    Importance: {rec.importance_score:.0%}")
        print(f"    Row count: {rec.row_count:,}")
        print(f"    Reason: {rec.reasoning}")
        print()
```

### Get Threshold Tuning Suggestions

```python
from anomalyarmor import Client

client = Client()

# Get threshold adjustment suggestions based on alert history
suggestions = client.recommendations.thresholds(
    asset_id="asset-uuid",
    days=30
)

print(f"Threshold Tuning Suggestions ({len(suggestions.recommendations)}):")
print()

for rec in suggestions.recommendations:
    print(f"Table: {rec.table_path}")
    print(f"  Current threshold: {rec.current_threshold}")
    print(f"  Suggested threshold: {rec.suggested_threshold}")
    print(f"  Direction: {rec.direction}")
    print(f"  Historical alerts: {rec.historical_alerts}")
    print(f"  Projected reduction: {rec.projected_reduction}")
    print(f"  Confidence: {rec.confidence:.0%}")
    print(f"  Reason: {rec.reasoning}")
    print()
```

## Recommendation Types

| Type | What It Recommends | Based On |
|------|-------------------|----------|
| Freshness | Tables + thresholds for freshness monitoring | Update patterns, confidence |
| Metrics | Quality checks per column | Column types, naming patterns |
| Coverage | Unmonitored high-value tables | Row count, importance score |
| Thresholds | Adjustments to reduce alert fatigue | Historical alert data |

## Importance Factors

The recommendation engine considers:
- **Update patterns**: Detected frequency and regularity
- **Column types**: Numeric, string, datetime patterns
- **Naming patterns**: `*_id`, `*_count`, `*_amount` conventions
- **Historical alerts**: False positive/negative rates
- **Table size**: Row count as importance proxy

## Follow-up Actions

- For freshness recommendations: Use `/armor:test` then `/armor:monitor`
- For metrics recommendations: Use `/armor:quality` to create metrics
- For coverage gaps: Prioritize by importance score
- For threshold tuning: Apply via `/armor:monitor`

## Integration with Other Skills

- `/armor:recommend` -> Get suggestions
- `/armor:test` -> Dry-run suggested thresholds
- `/armor:monitor` -> Enable if dry-run looks good
- `/armor:coverage` -> See current coverage status
