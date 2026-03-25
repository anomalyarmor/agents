"""Asset management tools.

Consolidates all asset operations (previously split between health.py and here).
list_assets and trigger_asset_discovery moved from health.py for SRP.
"""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"assets", "read"},
)
@sdk_tool
async def list_assets(
    asset_type: str | None = None,
    limit: int = 25,
):
    """List all connected data assets (databases, warehouses).

    Returns asset IDs needed by most other tools. Start here to find
    asset UUIDs for use with check_freshness, list_metrics, explore, etc.

    Args:
        asset_type: Filter by type ("postgresql", "snowflake", "bigquery", etc.)
        limit: Maximum results (default 25)
    """
    client = _get_client()
    return await asyncio.to_thread(client.assets.list, asset_type=asset_type, limit=limit)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"assets", "write"},
)
@sdk_tool
async def trigger_asset_discovery(asset_id: str):
    """Start schema discovery for an asset. Discovers all schemas, tables,
    columns, and metadata. Runs as background job.

    Use job_status() to track progress, then explore() to browse results.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    client = _get_client()
    return await asyncio.to_thread(client.assets.trigger_discovery, asset_id)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"assets", "write"},
)
@sdk_tool
async def create_asset(
    name: str,
    source_type: str,
    connection_config: dict,
    description: str | None = None,
):
    """Connect a new data source to AnomalyArmor.

    After creating, use trigger_asset_discovery to discover tables and columns.

    Args:
        name: Display name for the asset (e.g., "Production PostgreSQL")
        source_type: Database type: "postgresql", "snowflake", "bigquery",
                     "redshift", "mysql", "databricks"
        connection_config: Connection details (varies by source_type). Examples:
                    PostgreSQL: {"host": "...", "port": 5432, "database": "...",
                                 "username": "...", "password": "..."}
                    Snowflake: {"account": "...", "warehouse": "...",
                                "database": "...", "username": "...", "password": "..."}
        description: Optional description of the data source
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.assets.create,
        name=name,
        source_type=source_type,
        connection_config=connection_config,
        description=description,
    )


_VALID_ASSET_ACTIONS = ("get", "test")


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"assets", "read"},
)
@sdk_tool
async def manage_asset(
    action: str,
    asset_id: str,
):
    """Get asset details or test its connection.

    Args:
        action: Operation to perform:
                "get" - get full asset details including schema, table count, etc.
                "test" - test the database connection is working
        asset_id: Asset UUID (from list_assets)
    """
    if action not in _VALID_ASSET_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. " f"Must be: {', '.join(_VALID_ASSET_ACTIONS)}"
        )

    client = _get_client()

    if action == "get":
        return await asyncio.to_thread(client.assets.get, asset_id)
    elif action == "test":
        return await asyncio.to_thread(client.assets.test_connection, asset_id)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_ASSET_ACTIONS"
        )
