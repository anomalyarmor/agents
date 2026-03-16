"""Catalog tools: lineage, jobs, and tags."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

# -- Lineage -----------------------------------------------------------------


@mcp.tool()
@sdk_tool
def get_lineage(
    asset_id: str,
    depth: int = 2,
    direction: str = "both",
):
    """Get data lineage for an asset showing upstream sources and downstream consumers.

    Requires a dbt manifest to be uploaded via the UI or API.

    Args:
        asset_id: Asset UUID (from list_assets)
        depth: How many hops to traverse (default 2)
        direction: Lineage direction: "upstream", "downstream", or "both" (default "both")
    """
    return _get_client().lineage.get(
        asset_id=asset_id,
        depth=depth,
        direction=direction,
    )


# -- Jobs --------------------------------------------------------------------


@mcp.tool()
@sdk_tool
def job_status(job_id: str):
    """Check status of an async job (discovery, intelligence generation, etc.).

    Args:
        job_id: Job UUID (from trigger_asset_discovery, generate_intelligence, etc.)
    """
    return _get_client().jobs.get(job_id)


# -- Tags --------------------------------------------------------------------


@mcp.tool()
@sdk_tool
def list_tags(asset_id: str, object_path: str | None = None):
    """List tags applied to database objects within an asset.

    Use explore to find valid object paths.

    Args:
        asset_id: Asset UUID (from list_assets)
        object_path: Filter to tags on a specific object (e.g., "public.users.email")
    """
    return _get_client().tags.list(asset_id=asset_id, object_path=object_path)


@mcp.tool()
@sdk_tool
def apply_tags(
    asset_id: str,
    object_path: str,
    tags: list[str],
    object_type: str = "column",
):
    """Apply tags to a database object (table, column, schema).

    Use explore to find valid object paths before tagging.

    Args:
        asset_id: Asset UUID (from list_assets)
        object_path: Full path to the object (e.g., "public.users.email")
        tags: List of tag names to apply (e.g., ["pii", "revenue-critical"])
        object_type: Type of database object: "column", "table", or "schema"
    """
    return _get_client().tags.apply(
        asset_id=asset_id,
        object_path=object_path,
        tags=tags,
        object_type=object_type,
    )
