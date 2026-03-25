"""Referential integrity tools."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"referential", "write"},
)
@sdk_tool
async def create_referential_check(
    asset_id: str,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    name: str | None = None,
    severity: str = "warning",
):
    """Create a referential integrity check between two columns.

    Detects orphaned foreign key references. Use explore to find table
    and column names.

    Args:
        asset_id: Asset UUID (from list_assets)
        source_table: Table containing the foreign key (e.g., "public.orders")
        source_column: Foreign key column (e.g., "customer_id")
        target_table: Referenced table (e.g., "public.customers")
        target_column: Referenced column (e.g., "id")
        name: Human-readable name (auto-generated if omitted)
        severity: Alert severity: "warning" (default), "error", "critical"
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.referential.create,
        asset_id=asset_id,
        source_table=source_table,
        source_column=source_column,
        target_table=target_table,
        target_column=target_column,
        name=name,
        severity=severity,
    )


_VALID_REFERENTIAL_ACTIONS = (
    "summary",
    "list",
    "get",
    "update",
    "delete",
    "execute",
    "results",
)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True),
    tags={"referential", "delete"},
)
@sdk_tool
async def manage_referential(
    action: str,
    asset_id: str,
    check_id: str | None = None,
    name: str | None = None,
    severity: str | None = None,
    is_active: bool | None = None,
    limit: int = 25,
):
    """Manage referential integrity checks: view, update, delete, execute, or get results.

    Use create_referential_check to create new checks.

    Args:
        action: Operation to perform:
                "summary" - get overview of all checks for the asset
                "list" - list all checks for the asset
                "get" - get details of a specific check (requires check_id)
                "update" - update check settings (requires check_id)
                "delete" - delete a check (requires check_id)
                "execute" - run a check now (requires check_id)
                "results" - get recent results for a check (requires check_id)
        asset_id: Asset UUID (from list_assets)
        check_id: Check UUID (required for get/update/delete/execute/results)
        name: New name (for update action)
        severity: New severity (for update action)
        is_active: Enable/disable (for update action)
        limit: Max results (for list/results actions, default 25)
    """
    if action not in _VALID_REFERENTIAL_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_REFERENTIAL_ACTIONS)}"
        )

    client = _get_client()

    if action == "summary":
        return await asyncio.to_thread(client.referential.summary, asset_id)
    elif action == "list":
        return await asyncio.to_thread(
            client.referential.list, asset_id=asset_id, limit=limit
        )
    elif action == "get":
        if not check_id:
            raise ValueError("check_id is required for 'get' action")
        return await asyncio.to_thread(client.referential.get, asset_id, check_id)
    elif action == "update":
        if not check_id:
            raise ValueError("check_id is required for 'update' action")
        return await asyncio.to_thread(
            client.referential.update,
            asset_id=asset_id,
            check_id=check_id,
            name=name,
            severity=severity,
            is_active=is_active,
        )
    elif action == "delete":
        if not check_id:
            raise ValueError("check_id is required for 'delete' action")
        return await asyncio.to_thread(client.referential.delete, asset_id, check_id)
    elif action == "execute":
        if not check_id:
            raise ValueError("check_id is required for 'execute' action")
        return await asyncio.to_thread(client.referential.execute, asset_id, check_id)
    elif action == "results":
        if not check_id:
            raise ValueError("check_id is required for 'results' action")
        return await asyncio.to_thread(
            client.referential.results, asset_id, check_id, limit=limit
        )
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_REFERENTIAL_ACTIONS"
        )
