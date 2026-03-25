"""Catalog tools: lineage, jobs, and tags."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

# -- Lineage -----------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"lineage", "read"})
@sdk_tool
async def get_lineage(
    asset_id: str,
    depth: int = 2,
    direction: str = "both",
    list_all: bool = False,
):
    """Get data lineage for an asset showing upstream sources and downstream consumers.

    Requires a dbt manifest to be uploaded via the UI or API.

    Args:
        asset_id: Asset UUID (from list_assets)
        depth: How many hops to traverse (default 2)
        direction: Lineage direction: "upstream", "downstream", or "both" (default "both")
        list_all: List all lineage entries for the asset instead of graph view (default False)
    """
    client = _get_client()
    if list_all:
        return await asyncio.to_thread(client.lineage.list, asset_id=asset_id)
    return await asyncio.to_thread(
        client.lineage.get,
        asset_id=asset_id,
        depth=depth,
        direction=direction,
    )


# -- Jobs --------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"catalog", "read"})
@sdk_tool
async def job_status(job_id: str):
    """Check status of an async job (discovery, intelligence generation, etc.).

    Args:
        job_id: Job UUID (from trigger_asset_discovery, generate_intelligence, etc.)
    """
    client = _get_client()
    return await asyncio.to_thread(client.jobs.get, job_id)


# -- Tags --------------------------------------------------------------------


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"catalog", "write"})
@sdk_tool
async def create_tag(
    name: str,
    description: str | None = None,
    color: str | None = None,
):
    """Create a new tag for labeling database objects.

    After creating, use apply_tags to attach it to tables or columns.

    Args:
        name: Tag name (e.g., "pii", "revenue-critical", "deprecated")
        description: Optional description of the tag's purpose
        color: Optional hex color code (e.g., "#FF5733")
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.tags.create,
        name=name,
        description=description,
        color=color,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"catalog", "read"})
@sdk_tool
async def list_tags(asset_id: str, object_path: str | None = None):
    """List tags applied to database objects within an asset.

    Use explore to find valid object paths.

    Args:
        asset_id: Asset UUID (from list_assets)
        object_path: Filter to tags on a specific object (e.g., "public.users.email")
    """
    client = _get_client()
    return await asyncio.to_thread(client.tags.list, asset_id=asset_id, object_path=object_path)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"catalog", "write"})
@sdk_tool
async def apply_tags(
    asset_id: str,
    object_path: str | None = None,
    tags: list[str] | None = None,
    object_type: str = "column",
    asset_ids: list[str] | None = None,
):
    """Apply tags to database objects. Supports single or cross-asset bulk tagging.

    Use explore to find valid object paths before tagging.

    Args:
        asset_id: Asset UUID (from list_assets)
        object_path: Full path to the object (e.g., "public.users.email")
        tags: List of tag names to apply (e.g., ["pii", "revenue-critical"])
        object_type: Type of database object: "column", "table", or "schema"
        asset_ids: Apply tags across multiple assets (for bulk apply, overrides asset_id)
    """
    client = _get_client()

    if asset_ids:
        return await asyncio.to_thread(
            client.tags.bulk_apply,
            asset_ids=asset_ids,
            tags=tags or [],
            object_type=object_type,
        )

    if not object_path:
        raise ValueError("object_path is required for single-asset tagging")
    if not tags:
        raise ValueError("tags list is required")

    return await asyncio.to_thread(
        client.tags.apply,
        asset_id=asset_id,
        object_path=object_path,
        tags=tags,
        object_type=object_type,
    )
