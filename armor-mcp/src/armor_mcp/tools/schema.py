"""Schema monitoring tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def get_schema_summary():
    """Get schema drift summary with total changes, unacknowledged count, and severity breakdown.

    For individual changes use list_schema_changes.
    """
    return _get_client().schema.summary()


@mcp.tool()
@sdk_tool
def list_schema_changes(
    asset_id: str | None = None,
    severity: str | None = None,
    unacknowledged_only: bool = False,
    limit: int = 25,
):
    """List recent schema changes showing change type, severity, and acknowledgment status.

    For summary counts use get_schema_summary. To enable monitoring use
    enable_schema_monitoring.

    Args:
        asset_id: Filter by asset UUID (from list_assets)
        severity: Filter by severity: "critical", "warning", "info"
        unacknowledged_only: Only return unacknowledged changes (default false)
        limit: Maximum results (default 25)
    """
    return _get_client().schema.changes(
        asset_id=asset_id,
        severity=severity,
        unacknowledged_only=unacknowledged_only,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def create_schema_baseline(asset_id: str, description: str | None = None):
    """Capture current schema as baseline for drift detection.

    Required before enable_schema_monitoring can detect changes.

    Args:
        asset_id: Asset UUID (from list_assets)
        description: Optional description for the baseline
    """
    return _get_client().schema.create_baseline(asset_id, description=description)


@mcp.tool()
@sdk_tool
def enable_schema_monitoring(
    asset_id: str,
    schedule_type: str = "1d",
    auto_create_baseline: bool = True,
):
    """Enable schema drift monitoring for an asset.

    Detects column additions, removals, type changes, and other schema
    modifications. Use list_schema_changes to view detected changes.

    Args:
        asset_id: Asset UUID (from list_assets)
        schedule_type: How often to check for drift: "5m", "1h", "6h", "1d", "1w"
        auto_create_baseline: Create baseline if none exists (default True)
    """
    return _get_client().schema.enable_monitoring(
        asset_id=asset_id,
        schedule_type=schedule_type,
        auto_create_baseline=auto_create_baseline,
    )


@mcp.tool()
@sdk_tool
def disable_schema_monitoring(asset_id: str):
    """Disable schema drift monitoring for an asset. Keeps baseline for re-enabling.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().schema.disable_monitoring(asset_id)


@mcp.tool()
@sdk_tool
def get_schema_monitoring(asset_id: str):
    """Get schema monitoring configuration for an asset.

    Shows whether monitoring is enabled, schedule type, baseline info,
    and last check timestamp.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().schema.get(asset_id)


@mcp.tool()
@sdk_tool
def dry_run_schema(asset_id: str, schedule_type: str = "1d"):
    """Preview schema drift detection without persisting. Compares current
    schema against baseline to show what changes would be detected.

    Use this to test before enabling monitoring.

    Args:
        asset_id: Asset UUID (from list_assets)
        schedule_type: Schedule for alert estimation: "1h", "1d", "1w"
    """
    return _get_client().schema.dry_run(
        asset_id=asset_id,
        schedule_type=schedule_type,
    )
