"""Intelligence tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool()
@sdk_tool
def ask_question(
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
    return _get_client().intelligence.ask(
        question=question,
        asset_id=asset_id,
        include_schema=include_schema,
        include_lineage=include_lineage,
    )


@mcp.tool()
@sdk_tool
def generate_intelligence(
    asset_id: str,
    force_refresh: bool = False,
):
    """Generate AI analysis for an asset. Analyzes schema, data patterns,
    and metadata to generate insights. Results are cached.

    Runs as a background job. Use job_status to track progress.

    Args:
        asset_id: Asset UUID (from list_assets)
        force_refresh: Force regeneration even if cached (default False)
    """
    return _get_client().intelligence.generate(
        asset_id=asset_id,
        force_refresh=force_refresh,
    )
