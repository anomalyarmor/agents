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

    Args:
        asset_id: Asset UUID or qualified name
        depth: How many hops to traverse (default 2)
        direction: "upstream", "downstream", or "both" (default "both")
    """
    return _get_client().lineage.get(
        asset_id=asset_id, depth=depth, direction=direction,
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
    """List tags for an asset or specific object.

    Args:
        asset_id: Asset UUID or qualified name
        object_path: Optional object path to filter (e.g., "public.users.email")
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
    """Apply tags to a database object.

    Args:
        asset_id: Asset UUID or qualified name
        object_path: Object path (e.g., "public.users.email")
        tags: List of tag names to apply
        object_type: "column", "table", or "schema"
    """
    return _get_client().tags.apply(
        asset_id=asset_id,
        object_path=object_path,
        tags=tags,
        object_type=object_type,
    )
