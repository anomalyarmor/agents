"""Health & discovery tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def health_summary():
    """Start here for a quick overview of data health.

    Returns aggregated status across alerts, freshness, schema drift,
    metrics, and validity. For per-table details, use check_freshness
    or list_schema_changes.
    """
    return _get_client().health.summary()


@mcp.tool()
@sdk_tool
def list_assets(
    asset_type: str | None = None,
    limit: int = 25,
):
    """List all connected data assets (databases, warehouses).

    Returns asset IDs needed by most other tools. Start here to find
    asset UUIDs for use with check_freshness, list_metrics, explore, etc.

    Args:
        asset_type: Filter by type ("postgresql", "snowflake", "bigquery", etc.)
        limit: Maximum results (default 25)
    """
    return _get_client().assets.list(asset_type=asset_type, limit=limit)


@mcp.tool()
@sdk_tool
def trigger_asset_discovery(asset_id: str):
    """Start schema discovery for an asset. Discovers all schemas, tables,
    columns, and metadata. Runs as background job.

    Use job_status() to track progress, then explore() to browse results.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().assets.trigger_discovery(asset_id)
