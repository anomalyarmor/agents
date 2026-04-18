"""Schema monitoring tools."""

import asyncio
import json

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool
from armor_mcp.apps import render_app, to_plain
from mcp.types import TextContent, ToolAnnotations


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"schema", "read"},
)
@sdk_tool
async def get_schema_summary():
    """Get schema drift summary with total changes, unacknowledged count, and severity breakdown.

    For individual changes use list_schema_changes.
    """
    client = _get_client()
    return await asyncio.to_thread(client.schema.summary)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"schema", "read"},
)
@sdk_tool
async def list_schema_changes(
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
    client = _get_client()
    raw = await asyncio.to_thread(
        client.schema.changes,
        asset_id=asset_id,
        severity=severity,
        unacknowledged_only=unacknowledged_only,
        limit=limit,
    )
    payload = to_plain(raw)
    return [
        TextContent(type="text", text=json.dumps(payload, default=str)),
        render_app("schema_diff", payload),
    ]


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"schema", "write"})
@sdk_tool
async def create_schema_baseline(asset_id: str, description: str | None = None):
    """Capture current schema as baseline for drift detection.

    Required before enable_schema_monitoring can detect changes.

    Args:
        asset_id: Asset UUID (from list_assets)
        description: Optional description for the baseline
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.schema.create_baseline, asset_id, description=description
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"schema", "write"})
@sdk_tool
async def enable_schema_monitoring(
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
    client = _get_client()
    return await asyncio.to_thread(
        client.schema.enable_monitoring,
        asset_id=asset_id,
        schedule_type=schedule_type,
        auto_create_baseline=auto_create_baseline,
    )


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True), tags={"schema", "delete"})
@sdk_tool
async def disable_schema_monitoring(asset_id: str):
    """Disable schema drift monitoring for an asset. Keeps baseline for re-enabling.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    client = _get_client()
    return await asyncio.to_thread(client.schema.disable_monitoring, asset_id)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"schema", "read"},
)
@sdk_tool
async def get_schema_monitoring(asset_id: str):
    """Get schema monitoring configuration for an asset.

    Shows whether monitoring is enabled, schedule type, baseline info,
    and last check timestamp.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    client = _get_client()
    return await asyncio.to_thread(client.schema.get, asset_id)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"schema", "read"},
)
@sdk_tool
async def dry_run_schema(asset_id: str, schedule_type: str = "1d"):
    """Preview schema drift detection without persisting. Compares current
    schema against baseline to show what changes would be detected.

    Use this to test before enabling monitoring.

    Args:
        asset_id: Asset UUID (from list_assets)
        schedule_type: Schedule for alert estimation: "1h", "1d", "1w"
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.schema.dry_run,
        asset_id=asset_id,
        schedule_type=schedule_type,
    )
