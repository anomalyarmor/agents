"""Investigation tools (TECH-982).

Surfaces `client.investigations.{explain, get}` to MCP clients. Returns
an EvidenceCapsule: a typed projection of an AlertInvestigation that
cites each piece of evidence back to its source row (alert, schema
event, metric, lineage).

Replaces the previous five-step recipe that MCP-driven agents would
otherwise stitch together from health + freshness + lineage +
intelligence + alerts.
"""

import asyncio

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool
from mcp.types import ToolAnnotations


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=False),
    tags={"investigations", "read"},
    timeout=60.0,
)
@sdk_tool
async def investigate_asset(
    asset_id: str,
    question: str | None = None,
    event_type: str = "anomaly",
):
    """Run a synchronous root-cause investigation against an asset.

    Returns an EvidenceCapsule with root cause, triggers, consequences,
    confidence, and a suggested fix. Each piece of evidence is cited
    back to the underlying record (alert, schema event, metric, lineage)
    via `source` + `source_id` so the answer is auditable.

    Prefer this over composing multiple tools (freshness, lineage,
    intelligence) yourself: the backend already runs all of them in
    parallel inside the correlator pipeline.

    Args:
        asset_id: Asset UUID (from list_assets).
        question: Optional natural-language question to anchor the
            capsule (e.g. "Why is orders stale?"). Defaults to one
            derived from event_type.
        event_type: One of "anomaly", "freshness", "schema_change",
            "validity". Defaults to "anomaly".
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.investigations.explain,
        asset_id=asset_id,
        question=question,
        event_type=event_type,
    )


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"investigations", "read"},
)
@sdk_tool
async def get_investigation(investigation_id: str):
    """Fetch a persisted alert investigation and project it to a capsule.

    Use for alert-anchored investigations that already ran (typically
    triggered by an alert firing). For asset-level questions with no
    associated alert, use `investigate_asset` instead.

    Args:
        investigation_id: Investigation UUID.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.investigations.get,
        investigation_id=investigation_id,
    )
