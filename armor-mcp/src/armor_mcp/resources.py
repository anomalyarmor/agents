"""MCP resources for context loading.

Resources provide read-only data that clients can access without burning
a tool call. Useful for loading background context about data health,
assets, and monitoring status.
"""

from __future__ import annotations

import asyncio
import json

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import _serialize


@mcp.resource(
    "armor://health",
    description="Overall data health snapshot across alerts, freshness, schema drift, metrics, and validity",
    mime_type="application/json",
)
async def health_resource():
    client = _get_client()
    result = await asyncio.to_thread(client.health.summary)
    return json.dumps(_serialize(result))


@mcp.resource(
    "armor://assets",
    description="List of all connected data assets (databases, warehouses)",
    mime_type="application/json",
)
async def assets_resource():
    client = _get_client()
    result = await asyncio.to_thread(client.assets.list)
    return json.dumps(_serialize(result))


@mcp.resource(
    "armor://assets/{asset_id}/schema",
    description="Schema snapshot for a specific asset",
    mime_type="application/json",
)
async def asset_schema_resource(asset_id: str):
    client = _get_client()
    result = await asyncio.to_thread(client.schema.get, asset_id)
    return json.dumps(_serialize(result))


@mcp.resource(
    "armor://alerts/summary",
    description="Alert summary with counts by severity and status",
    mime_type="application/json",
)
async def alerts_summary_resource():
    client = _get_client()
    result = await asyncio.to_thread(client.alerts.summary)
    return json.dumps(_serialize(result))


@mcp.resource(
    "armor://freshness/summary",
    description="Freshness monitoring summary with stale table counts",
    mime_type="application/json",
)
async def freshness_summary_resource():
    client = _get_client()
    result = await asyncio.to_thread(client.freshness.summary)
    return json.dumps(_serialize(result))
