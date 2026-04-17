# Working with the AnomalyArmor MCP server

Project-specific guidance for Claude Code (and any compatible agent) when this repo's `armor-mcp` server is connected.

## Connect once

```bash
claude mcp add anomalyarmor --transport http https://mcp.anomalyarmor.ai/mcp
```

The first tool invocation opens a browser for OAuth. Subsequent calls reuse the cached token until it expires (~12h).

For local-only / air-gapped use:

```bash
pip install armor-mcp
ARMOR_API_KEY=aa_live_... armor-mcp
# or
uvx armor-mcp
```

## Tool categories

Tools are grouped by safety/cost. Treat them differently in autonomy:

| Category | Examples | Confirmation policy |
|----------|----------|---------------------|
| Read-only | `health_summary`, `list_alerts`, `get_lineage`, `check_freshness`, `search_documentation` | Auto-invoke freely |
| Mutating | `create_freshness_schedule`, `enable_schema_monitoring`, `acknowledge_alert`, `resolve_alert` | Confirm with user, especially for bulk |
| Destructive | `delete_*`, `dismiss_alert` | Always confirm. List affected entities first. |
| Expensive | `generate_intelligence`, `trigger_asset_discovery`, `capture_metric` | Confirm. These queue background jobs. |

Every tool has `ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`). Respect them.

## Default workflows

**Morning triage**

```
health_summary
list_alerts(severity=critical, status=open)
list_stale_assets()
```

For each critical alert, get context with `check_freshness` + `get_lineage` before recommending an action.

**Onboarding a new schema**

```
explore(asset_id, parent_path="<schema>")            # discover tables
setup_freshness(asset_id, schema_name, table_paths)  # bulk freshness
enable_schema_monitoring(asset_ids=[...])            # bulk drift detection
create_metric(...)                                    # one per ID/email column
```

Always confirm the table list with the user before bulk operations.

**Investigation**

```
check_freshness(table)
get_lineage(table)
list_schema_changes(asset_id, since="7d")
```

Trace upstream first to find the breaking change; then enumerate downstream to scope blast radius.

## Multi-tenancy

The server is scoped to the OAuth-authenticated user's company. You **cannot** access other tenants. Do not invent `company_id` arguments.

## Async jobs

`trigger_asset_discovery`, `capture_metric`, and `generate_intelligence` return a `job_id`. Poll with `job_status(job_id)` rather than re-invoking the trigger.

## Don't

- Don't loop `generate_intelligence` to retry. It costs LLM tokens. If it failed, read the error and adjust the prompt.
- Don't bulk-`delete_*` anything without echoing the full list of entities to the user first.
- Don't use the synchronous `ask_question` for bulk lookups. It is pay-per-call.

## More

- Full tool reference: https://docs.anomalyarmor.ai/integrations/mcp-server
- Repo guide: AGENTS.md (top of this repo)
