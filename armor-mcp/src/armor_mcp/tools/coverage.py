"""Coverage scoring and gap analysis tools."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"coverage", "read"},
)
@sdk_tool
async def get_coverage(
    scope: str = "company",
    asset_id: str | None = None,
):
    """Get monitoring coverage score and tier information.

    Shows how well your data assets are monitored with scores, tiers,
    and per-feature breakdowns.

    Args:
        scope: Coverage scope:
               "company" - company-wide rollup across all assets
               "asset" - per-asset score with feature breakdown (requires asset_id)
        asset_id: Asset UUID (required when scope="asset")
    """
    if scope not in ("company", "asset"):
        raise ValueError(f"Invalid scope '{scope}'. Must be 'company' or 'asset'.")

    client = _get_client()

    if scope == "company":
        return await asyncio.to_thread(client.coverage.company)
    elif scope == "asset":
        if not asset_id:
            raise ValueError("asset_id is required when scope='asset'")
        return await asyncio.to_thread(client.coverage.get, asset_id)
    else:
        raise ValueError(f"Unhandled scope '{scope}'")


_VALID_COVERAGE_ACTIONS = ("gaps", "apply")


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"coverage", "read", "write"},
)
@sdk_tool
async def manage_coverage(
    action: str,
    asset_id: str,
    limit: int = 20,
    types: list[str] | None = None,
    table_paths: list[str] | None = None,
):
    """Analyze coverage gaps or apply monitoring recommendations in batch.

    Use get_coverage to see current scores first.

    Args:
        action: Operation to perform:
                "gaps" - list unmonitored tables ranked by importance
                "apply" - apply recommended monitoring in batch
        asset_id: Asset UUID (from list_assets)
        limit: Maximum gap recommendations (for gaps action, default 20)
        types: Monitoring types to apply: "freshness", "metrics", "schema_drift"
               (for apply action, omit for all)
        table_paths: Limit to specific tables (for apply action, omit for all)
    """
    if action not in _VALID_COVERAGE_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_COVERAGE_ACTIONS)}"
        )

    client = _get_client()

    if action == "gaps":
        return await asyncio.to_thread(client.coverage.gaps, asset_id, limit=limit)
    elif action == "apply":
        return await asyncio.to_thread(
            client.coverage.apply, asset_id, types=types, table_paths=table_paths
        )
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_COVERAGE_ACTIONS"
        )
