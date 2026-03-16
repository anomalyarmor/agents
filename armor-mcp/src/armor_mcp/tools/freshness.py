"""Freshness monitoring tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def get_freshness_summary():
    """Get freshness monitoring summary with counts of fresh, stale, and unknown tables.

    For a quick overview use health_summary. For per-table details
    use check_freshness.
    """
    return _get_client().freshness.summary()


@mcp.tool()
@sdk_tool
def check_freshness(asset_id: str):
    """Check freshness status for all monitored tables in an asset.

    Shows which tables are fresh, stale, or unknown. Use setup_freshness
    to add monitoring for new tables.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().freshness.check(asset_id)


@mcp.tool()
@sdk_tool
def setup_freshness(
    asset_id: str,
    table_path: str,
    check_interval: str = "1h",
    expected_interval_hours: float | None = None,
    freshness_column: str | None = None,
    monitoring_mode: str = "auto_learn",
):
    """Create freshness monitoring for a table.

    Use explore to find table paths, recommend_freshness for suggested intervals.

    Args:
        asset_id: Asset UUID (from list_assets)
        table_path: Full table path (e.g., "public.orders")
        check_interval: How often to check: "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1d", "1w"
        expected_interval_hours: Hours until stale (required for explicit mode)
        freshness_column: Column to check (auto-detected if not provided)
        monitoring_mode: "auto_learn" (recommended, learns thresholds) or "explicit"
    """
    return _get_client().freshness.create_schedule(
        asset_id=asset_id,
        table_path=table_path,
        check_interval=check_interval,
        expected_interval_hours=expected_interval_hours,
        freshness_column=freshness_column,
        monitoring_mode=monitoring_mode,
    )


@mcp.tool()
@sdk_tool
def list_freshness_schedules(
    asset_id: str | None = None,
    limit: int = 25,
):
    """List freshness monitoring schedules showing check intervals and status.

    Use setup_freshness to add new schedules.

    Args:
        asset_id: Filter by asset UUID (from list_assets)
        limit: Maximum results (default 25)
    """
    return _get_client().freshness.list_schedules(asset_id=asset_id, limit=limit)
