"""Intelligence tools."""

import asyncio

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import _attr, sdk_tool


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
@sdk_tool
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

    job_id = _attr(job, "job_id")
    if not job_id:
        return job

    while True:
        status = await asyncio.to_thread(client.jobs.get, job_id)
        status_value = _attr(status, "status")
        progress = _attr(status, "progress")

        await ctx.report_progress(progress or 0, 100)
        await ctx.info(f"Intelligence generation: {status_value}")

        if status_value in ("completed", "failed", "cancelled", "timed_out", "error"):
            break
        await asyncio.sleep(3)

    if status_value != "completed":
        raise ToolError(f"Intelligence generation {status_value}: {_attr(status, 'error', 'unknown error')}")
    return status
