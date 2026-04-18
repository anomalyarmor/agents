"""Freshness monitoring tools."""

import asyncio
import json

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool
from armor_mcp.apps import render_app, to_plain
from mcp.types import TextContent, ToolAnnotations


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"freshness", "read"},
)
@sdk_tool
async def get_freshness_summary():
    """Get freshness monitoring summary with counts of fresh, stale, and unknown tables.

    For a quick overview use health_summary. For per-table details
    use check_freshness.
    """
    client = _get_client()
    raw = await asyncio.to_thread(client.freshness.summary)
    payload = to_plain(raw)
    return [
        TextContent(type="text", text=json.dumps(payload, default=str)),
        render_app("freshness_timeline", payload),
    ]


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"freshness", "read"},
)
@sdk_tool
async def check_freshness(
    asset_id: str,
    stale_only: bool = False,
):
    """Check freshness status for all monitored tables in an asset.

    Shows which tables are fresh, stale, or unknown. Use setup_freshness
    to add monitoring for new tables.

    Args:
        asset_id: Asset UUID (from list_assets)
        stale_only: Only return stale tables (default False)
    """
    client = _get_client()
    if stale_only:
        raw = await asyncio.to_thread(
            client.freshness.list, asset_id=asset_id, status="stale"
        )
    else:
        raw = await asyncio.to_thread(client.freshness.check, asset_id)
    payload = to_plain(raw)
    return [
        TextContent(type="text", text=json.dumps(payload, default=str)),
        render_app("freshness_timeline", payload),
    ]


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"freshness", "write"},
)
@sdk_tool
async def setup_freshness(
    asset_id: str,
    table_path: str | None = None,
    table_paths: list[str] | None = None,
    check_interval: str = "1h",
    expected_interval_hours: float | None = None,
    freshness_column: str | None = None,
    monitoring_mode: str = "auto_learn",
):
    """Create freshness monitoring for one or more tables.

    Use explore to find table paths, recommend_freshness for suggested intervals.

    Args:
        asset_id: Asset UUID (from list_assets)
        table_path: Single table path (e.g., "public.orders")
        table_paths: Multiple table paths for bulk setup (overrides table_path)
        check_interval: How often to check: "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1d", "1w"
        expected_interval_hours: Hours until stale (required for explicit mode)
        freshness_column: Column to check (auto-detected if not provided)
        monitoring_mode: "auto_learn" (recommended, learns thresholds) or "explicit"
    """
    client = _get_client()

    if table_paths:
        return await asyncio.to_thread(
            client.freshness.bulk_create_schedules,
            asset_id=asset_id,
            table_paths=table_paths,
            check_interval=check_interval,
            expected_interval_hours=expected_interval_hours,
            freshness_column=freshness_column,
            monitoring_mode=monitoring_mode,
        )

    if not table_path:
        raise ValueError("Either table_path or table_paths is required")

    return await asyncio.to_thread(
        client.freshness.create_schedule,
        asset_id=asset_id,
        table_path=table_path,
        check_interval=check_interval,
        expected_interval_hours=expected_interval_hours,
        freshness_column=freshness_column,
        monitoring_mode=monitoring_mode,
    )


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"freshness", "read"},
)
@sdk_tool
async def list_freshness_schedules(
    asset_id: str | None = None,
    limit: int = 25,
):
    """List freshness monitoring schedules showing check intervals and status.

    Use setup_freshness to add new schedules.

    Args:
        asset_id: Filter by asset UUID (from list_assets)
        limit: Maximum results (default 25)
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.freshness.list_schedules, asset_id=asset_id, limit=limit
    )


_VALID_SCHEDULE_ACTIONS = ("update", "delete")


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True),
    tags={"freshness", "write", "delete"},
)
@sdk_tool
async def manage_freshness_schedule(
    action: str,
    schedule_id: str,
    check_interval: str | None = None,
    expected_interval_hours: float | None = None,
    freshness_column: str | None = None,
    monitoring_mode: str | None = None,
    is_active: bool | None = None,
):
    """Update or delete a freshness monitoring schedule.

    Use list_freshness_schedules to find schedule IDs.

    Args:
        action: Operation: "update" or "delete"
        schedule_id: Schedule UUID (from list_freshness_schedules)
        check_interval: New check interval (for update)
        expected_interval_hours: New staleness threshold (for update)
        freshness_column: New column to check (for update)
        monitoring_mode: New mode: "auto_learn" or "explicit" (for update)
        is_active: Enable/disable schedule (for update)
    """
    if action not in _VALID_SCHEDULE_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_SCHEDULE_ACTIONS)}"
        )

    client = _get_client()

    if action == "update":
        return await asyncio.to_thread(
            client.freshness.update_schedule,
            schedule_id=schedule_id,
            check_interval=check_interval,
            expected_interval_hours=expected_interval_hours,
            freshness_column=freshness_column,
            monitoring_mode=monitoring_mode,
            is_active=is_active,
        )
    elif action == "delete":
        return await asyncio.to_thread(client.freshness.delete_schedule, schedule_id)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_SCHEDULE_ACTIONS"
        )
