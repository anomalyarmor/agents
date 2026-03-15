"""Schema monitoring tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def get_schema_summary():
    """Get schema drift summary across all assets.

    Returns counts of total changes, unacknowledged changes,
    and severity breakdown.
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
    """List schema changes with optional filters.

    Args:
        asset_id: Filter by asset UUID or qualified name
        severity: Filter by severity ("critical", "warning", "info")
        unacknowledged_only: Only return unacknowledged changes
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

    Args:
        asset_id: Asset UUID or qualified name
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

    Args:
        asset_id: Asset UUID or qualified name
        schedule_type: Check interval ("5m", "1h", "6h", "1d", "1w",
                       or legacy: "hourly", "daily", "weekly")
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
    """Disable schema drift monitoring for an asset (keeps baseline).

    Args:
        asset_id: Asset UUID or qualified name
    """
    return _get_client().schema.disable_monitoring(asset_id)


@mcp.tool()
@sdk_tool
def dry_run_schema(asset_id: str, schedule_type: str = "1d"):
    """Preview schema drift detection without persisting. Compares current
    schema against baseline to show what changes would be detected.

    Args:
        asset_id: Asset UUID or qualified name
        schedule_type: Schedule for alert estimation ("1h", "1d", "1w")
    """
    return _get_client().schema.dry_run(
        asset_id=asset_id, schedule_type=schedule_type,
    )
