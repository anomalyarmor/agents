"""Intelligence tools."""

import asyncio

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import _serialize, sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"intelligence", "read"},
)
@sdk_tool
async def ask_question(
    question: str,
    asset_id: str | None = None,
    include_schema: bool = True,
    include_lineage: bool = False,
):
    """Ask a natural language question about your data.

    Uses AI to analyze your schema, metadata, and monitoring data to answer.

    Args:
        question: Natural language question (e.g., "What tables contain customer PII?")
        asset_id: Asset UUID to scope the question (from list_assets). Omit for all assets.
        include_schema: Include schema info in context (default True)
        include_lineage: Include lineage info in context (default False)
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.intelligence.ask,
        question=question,
        asset_id=asset_id,
        include_schema=include_schema,
        include_lineage=include_lineage,
    )


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=True),
    tags={"intelligence", "write"},
    timeout=300.0,
)
async def generate_intelligence(
    asset_id: str,
    force_refresh: bool = False,
    ctx: Context = CurrentContext(),
):
    """Generate AI analysis for an asset. Analyzes schema, data patterns,
    and metadata to generate insights. Results are cached.

    Runs as a background job with progress reporting.

    Args:
        asset_id: Asset UUID (from list_assets)
        force_refresh: Force regeneration even if cached (default False)
    """
    client = _get_client()
    job = await asyncio.to_thread(
        client.intelligence.generate,
        asset_id=asset_id,
        force_refresh=force_refresh,
    )

    job_id = job.job_id if hasattr(job, "job_id") else job.get("job_id") if isinstance(job, dict) else None
    if not job_id:
        return _serialize(job)

    while True:
        status = await asyncio.to_thread(client.jobs.status, job_id)
        status_value = status.status if hasattr(status, "status") else status.get("status") if isinstance(status, dict) else None
        progress = status.progress if hasattr(status, "progress") else status.get("progress") if isinstance(status, dict) else None

        await ctx.report_progress(progress or 0, 100)
        await ctx.info(f"Intelligence generation: {status_value}")

        if status_value in ("completed", "failed"):
            break
        await asyncio.sleep(3)

    if status_value == "failed":
        error_msg = status.error if hasattr(status, "error") else status.get("error") if isinstance(status, dict) else "unknown error"
        raise ToolError(f"Intelligence generation failed: {error_msg}")
    return _serialize(status)
