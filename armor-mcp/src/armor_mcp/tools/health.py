"""Health & discovery tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def health_summary():
    """Get overall health status of monitored data assets.

    Returns aggregated status across alerts, freshness, schema drift,
    metrics, and validity. Use this as the first call when checking
    "is my data healthy?"
    """
    return _get_client().health.summary()


@mcp.tool()
@sdk_tool
def list_assets(
    asset_type: str | None = None,
    limit: int = 25,
):
    """List connected data sources (databases, warehouses).

    Args:
        asset_type: Filter by type ("postgresql", "snowflake", "bigquery", etc.)
        limit: Maximum results (default 25)
    """
    return _get_client().assets.list(asset_type=asset_type, limit=limit)


@mcp.tool()
@sdk_tool
def trigger_asset_discovery(asset_id: str):
    """Start schema discovery for an asset. Discovers all schemas, tables,
    columns, and metadata. Runs as background job - use job_status() to track.

    Args:
        asset_id: Asset UUID or qualified name
    """
    return _get_client().assets.trigger_discovery(asset_id)
