"""Recommendation tools for AI-driven monitoring suggestions."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

_VALID_RECOMMEND_TYPES = ("freshness", "metrics", "coverage", "thresholds")


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"recommendations", "read"},
)
@sdk_tool
async def recommend(
    recommendation_type: str,
    asset_id: str,
    limit: int = 20,
    min_confidence: float = 0.5,
    include_monitored: bool = False,
    table_path: str | None = None,
    days: int = 30,
):
    """Get AI-driven monitoring recommendations for an asset.

    Analyzes historical patterns, schema, and alert data to suggest
    monitoring improvements.

    Args:
        recommendation_type: Type of recommendation:
                "freshness" - suggest tables and thresholds for freshness monitoring
                "metrics" - suggest quality metrics based on column analysis
                "coverage" - identify unmonitored tables ranked by importance
                "thresholds" - suggest threshold adjustments to reduce alert fatigue
        asset_id: Asset UUID (from list_assets)
        limit: Maximum recommendations (default 20)
        min_confidence: Minimum confidence threshold 0.0-1.0 (for freshness/metrics, default 0.5)
        include_monitored: Include already-monitored tables (for freshness, default False)
        table_path: Filter to specific table (for metrics)
        days: Historical window in days (for thresholds, default 30)
    """
    if recommendation_type not in _VALID_RECOMMEND_TYPES:
        raise ValueError(
            f"Invalid type '{recommendation_type}'. "
            f"Must be: {', '.join(_VALID_RECOMMEND_TYPES)}"
        )

    client = _get_client()

    if recommendation_type == "freshness":
        return await asyncio.to_thread(
            client.recommendations.freshness,
            asset_id,
            min_confidence=min_confidence,
            limit=limit,
            include_monitored=include_monitored,
        )
    elif recommendation_type == "metrics":
        return await asyncio.to_thread(
            client.recommendations.metrics,
            asset_id,
            table_path=table_path,
            min_confidence=min_confidence,
            limit=limit,
        )
    elif recommendation_type == "coverage":
        return await asyncio.to_thread(
            client.recommendations.coverage,
            asset_id,
            limit=limit,
        )
    elif recommendation_type == "thresholds":
        return await asyncio.to_thread(
            client.recommendations.thresholds,
            asset_id,
            days=days,
            limit=limit,
        )
    else:
        raise ValueError(
            f"Unhandled type '{recommendation_type}', "
            f"update dispatch to match _VALID_RECOMMEND_TYPES"
        )
