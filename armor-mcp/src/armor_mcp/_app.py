"""FastMCP application instance.

Separated from server.py to avoid circular imports when tool modules
need to register on the mcp instance.

The `instructions` block is the text returned in the MCP `Initialize`
response and shown to the host (Claude Desktop, Cursor, Claude Code).
Keep this in sync with the server-card document at
www.anomalyarmor.ai/.well-known/mcp/server-card.json.
"""

from fastmcp import FastMCP

_INSTRUCTIONS = """\
Use these tools to monitor data quality and incidents in the user's data \
warehouse. Start with `health_summary` to get an overall picture before \
drilling in. Prefer `list_alerts` over `list_inbox_alerts` for fresh \
state; `get_alerts_summary` for trends. When investigating root cause, \
follow `check_freshness` -> `get_lineage` to trace upstream/downstream \
impact. For setup tasks (freshness, schema baselines, validity rules), \
always confirm with the user before bulk-applying changes. The MCP \
server is multi-tenant and scoped to the authenticated user's company; \
never expose data outside that scope. Tools are categorized as \
read-only (`list_*`, `get_*`, `check_*`), mutating (`create_*`, \
`manage_*`, `update_*`, `enable_*`, `disable_*`, `setup_*`), or \
expensive (`generate_intelligence`, `trigger_asset_discovery`); \
rate-limit aggressively and confirm before invoking expensive ones. \
Async tools return a job_id -- poll with `job_status(job_id)` rather \
than re-triggering."""

mcp = FastMCP(
    "armor-mcp",
    instructions=_INSTRUCTIONS,
    mask_error_details=True,
)
