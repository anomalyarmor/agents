---
name: armor-coverage
description: Analyze monitoring coverage, tiers, and gaps. Handles what am I monitoring, what tier am I at, coverage gaps, monitoring status, unmonitored tables, how do I improve coverage.
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py
          once: true
---

# Monitoring Coverage and Tiers

Analyze what is being monitored, view your coverage tier, and identify gaps in your data observability.

## Prerequisites

- AnomalyArmor API key configured
- Python SDK installed (pip install anomalyarmor)

## When to Use

- What am I monitoring?
- What tier is my database at?
- Show monitoring gaps
- How do I improve my coverage score?
- What tables have no alerts?

## Coverage Tiers

Every asset earns a coverage score (0-100) based on 6 monitoring features:

| Tier | Score | What You Catch |
|------|-------|---------------|
| Monitored | 10-29 | Schema changes that break pipelines |
| Protected | 30-49 | Pipeline failures, data disappearing |
| Verified | 50-69 | Stale data, value corruption |
| Intelligent | 70+ | AI-powered anomaly detection |

Score weights: Schema Drift (25%), Freshness (25%), Metrics (20%), Alert Routing (15%), Validity (10%), Intelligence (5%).

## Steps

### Get Coverage Score and Tier

Use client.coverage.get(asset_id) to get score, tier, and breakdown.

### Get Company-Wide Coverage

Use client.coverage.company() for company rollup with per-asset scores.

### Find Coverage Gaps

Use client.coverage.gaps(asset_id) for prioritized recommendations.

### Apply Recommendations

Use client.coverage.apply(asset_id) to batch-apply all recommendations.

## Related Skills

- /armor:recommend - Get AI-driven recommendations for what to monitor
- /armor:monitor - Set up freshness and schema monitoring
- /armor:quality - Add metrics and validity rules
