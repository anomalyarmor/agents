"""AnomalyArmor MCP Server.

This module provides an MCP server that wraps the AnomalyArmor Python SDK,
exposing data observability tools to AI assistants like Claude Code and Cursor.

Usage:
    uvx armor-mcp
    # or
    python -m armor_mcp.server
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from fastmcp import FastMCP

mcp = FastMCP("armor-mcp", description="AnomalyArmor Data Observability Tools")

T = TypeVar("T")

# Singleton client instance
_client: Any = None


def _get_client() -> Any:
    """Get or create singleton SDK client.

    Returns:
        Initialized AnomalyArmor Client instance.

    Raises:
        RuntimeError: If SDK is not installed or API key is not configured.
    """
    global _client
    if _client is None:
        try:
            from anomalyarmor import Client
            from anomalyarmor.exceptions import AuthenticationError
        except ImportError as e:
            raise RuntimeError(
                "anomalyarmor SDK not installed. Run: pip install anomalyarmor"
            ) from e

        try:
            _client = Client()
        except AuthenticationError as e:
            raise RuntimeError(
                "No API key configured. Set ARMOR_API_KEY env var or create ~/.armor/config.yaml"
            ) from e

    return _client


def sdk_tool(func: Callable[..., T]) -> Callable[..., dict | list[dict]]:
    """Decorator for SDK-wrapping tools.

    Handles:
    - Pydantic model serialization via model_dump()
    - Error handling with structured error responses
    - List serialization

    Args:
        func: Tool function that returns SDK model or list of models.

    Returns:
        Wrapped function returning dict or list of dicts.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict | list[dict]:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, list):
                return [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in result
                ]
            if hasattr(result, "model_dump"):
                return result.model_dump()
            if isinstance(result, dict):
                return result
            return {"result": result}
        except Exception as e:
            error_type = type(e).__name__
            return {"error": error_type, "message": str(e)}

    return wrapper


# ============================================================================
# Health Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def health_summary():
    """Get overall health status of monitored data assets.

    Returns aggregated status across alerts, freshness, and schema drift.
    Use this as the first call when checking "is my data healthy?"

    Returns:
        Health summary with overall_status, component summaries, and needs_attention items.
    """
    return _get_client().health.summary()


# ============================================================================
# Alert Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    asset_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 25,
):
    """List alerts with optional filtering.

    Args:
        status: Filter by status ("triggered", "acknowledged", "resolved")
        severity: Filter by severity ("info", "warning", "critical")
        asset_id: Filter by asset UUID or qualified name
        from_date: Start of date range (ISO 8601 format, e.g., "2026-01-29T00:00:00Z")
        to_date: End of date range (ISO 8601 format)
        limit: Maximum number of results (default 25, max 100)

    Returns:
        List of alerts matching the filters.

    Example:
        "What alerts fired yesterday?" -> from_date="2026-01-29T00:00:00Z"
    """
    return _get_client().alerts.list(
        status=status,
        severity=severity,
        asset_id=asset_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def get_alert_summary():
    """Get summary of alerts across all assets.

    Returns:
        Alert summary with counts of total rules, active rules, recent alerts, and unresolved alerts.
    """
    return _get_client().alerts.summary()


# ============================================================================
# Asset Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def list_assets(
    source: str | None = None,
    asset_type: str | None = None,
    search: str | None = None,
    limit: int = 50,
):
    """List monitored assets with optional filters.

    Args:
        source: Filter by source type ("postgresql", "snowflake", "databricks", etc.)
        asset_type: Filter by asset type ("table", "view")
        search: Search in asset names
        limit: Maximum results (default 50, max 100)

    Returns:
        List of assets matching the filters.
    """
    return _get_client().assets.list(
        source=source,
        asset_type=asset_type,
        search=search,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def get_asset(asset_id: str):
    """Get details for a specific asset.

    Args:
        asset_id: Asset UUID or qualified name (e.g., "postgresql.mydb.public.users")

    Returns:
        Asset details including name, source, schema, and monitoring status.
    """
    return _get_client().assets.get(asset_id)


@mcp.tool()
@sdk_tool
def create_asset(
    name: str,
    source_type: str,
    connection_config: dict,
    description: str | None = None,
):
    """Create a new data source connection.

    Args:
        name: Display name for the asset
        source_type: Database type ("snowflake", "postgresql", "databricks", "bigquery", "redshift", "mysql", "clickhouse")
        connection_config: Connection parameters (varies by source_type)
        description: Optional description

    Returns:
        Created asset with id for subsequent operations.

    Example connection_config for Snowflake:
        {"account": "abc123.us-east-1", "warehouse": "COMPUTE_WH", "database": "ANALYTICS", "user": "user", "password": "..."}
    """
    return _get_client().assets.create(
        name=name,
        source_type=source_type,
        connection_config=connection_config,
        description=description,
    )


@mcp.tool()
@sdk_tool
def test_asset_connection(asset_id: str):
    """Test connection to a data source.

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Connection test result with success status and error details if failed.
    """
    return _get_client().assets.test_connection(asset_id)


@mcp.tool()
@sdk_tool
def trigger_asset_discovery(asset_id: str):
    """Trigger schema discovery for an asset.

    Starts an async job that crawls the data source to discover tables, columns, and metadata.
    Use job_status() to track progress.

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Discovery job with job_id for tracking progress.
    """
    return _get_client().assets.trigger_discovery(asset_id)


# ============================================================================
# Freshness Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def get_freshness_summary():
    """Get freshness summary across all assets.

    Returns:
        Summary with counts of fresh, stale, unknown, and disabled assets, plus freshness rate.
    """
    return _get_client().freshness.summary()


@mcp.tool()
@sdk_tool
def check_freshness(asset_id: str):
    """Check freshness status for a specific asset.

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Freshness status including is_stale, last_update_time, hours_since_update.
    """
    return _get_client().freshness.get(asset_id)


@mcp.tool()
@sdk_tool
def list_stale_assets(limit: int = 25):
    """List assets that are currently stale.

    Args:
        limit: Maximum results (default 25)

    Returns:
        List of stale assets with their freshness details.
    """
    return _get_client().freshness.list(status="stale", limit=limit)


@mcp.tool()
@sdk_tool
def list_freshness_schedules(
    asset_id: str | None = None,
    active_only: bool = False,
    limit: int = 50,
):
    """List freshness monitoring schedules.

    Args:
        asset_id: Filter by asset UUID or qualified name
        active_only: Only return active schedules
        limit: Maximum results (default 50)

    Returns:
        List of freshness schedules.
    """
    return _get_client().freshness.list_schedules(
        asset_id=asset_id,
        active_only=active_only,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def create_freshness_schedule(
    asset_id: str,
    table_path: str,
    check_interval: str,
    expected_interval_hours: float | None = None,
    freshness_column: str | None = None,
    monitoring_mode: str = "auto_learn",
):
    """Create a freshness monitoring schedule.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.orders")
        check_interval: Check frequency ("5m", "1h", "6h", "1d", "1w")
        expected_interval_hours: Hours until stale (required for explicit mode)
        freshness_column: Column to check (auto-detected if not provided)
        monitoring_mode: "auto_learn" (recommended) or "explicit"

    Returns:
        Created freshness schedule.

    Example:
        create_freshness_schedule("asset-uuid", "public.orders", "1h")
    """
    return _get_client().freshness.create_schedule(
        asset_id=asset_id,
        table_path=table_path,
        check_interval=check_interval,
        expected_interval_hours=expected_interval_hours,
        freshness_column=freshness_column,
        monitoring_mode=monitoring_mode,
    )


@mcp.tool()
@sdk_tool
def delete_freshness_schedule(schedule_id: str):
    """Delete a freshness schedule.

    Args:
        schedule_id: Schedule UUID

    Returns:
        Deletion confirmation.
    """
    return _get_client().freshness.delete_schedule(schedule_id)


# ============================================================================
# Schema Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def get_schema_summary():
    """Get schema drift summary across all assets.

    Returns:
        Summary with counts of total changes, unacknowledged changes, and severity breakdown.
    """
    return _get_client().schema.summary()


@mcp.tool()
@sdk_tool
def list_schema_changes(
    asset_id: str | None = None,
    severity: str | None = None,
    unacknowledged_only: bool = False,
    limit: int = 25,
):
    """List schema changes with optional filters.

    Args:
        asset_id: Filter by asset UUID or qualified name
        severity: Filter by severity ("critical", "warning", "info")
        unacknowledged_only: Only return unacknowledged changes
        limit: Maximum results (default 25)

    Returns:
        List of schema changes.
    """
    return _get_client().schema.changes(
        asset_id=asset_id,
        severity=severity,
        unacknowledged_only=unacknowledged_only,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def create_schema_baseline(asset_id: str, description: str | None = None):
    """Create a schema baseline for drift detection.

    Captures the current schema as the baseline for future drift detection.

    Args:
        asset_id: Asset UUID or qualified name
        description: Optional description for the baseline

    Returns:
        Created baseline with captured schema info.
    """
    return _get_client().schema.create_baseline(asset_id, description=description)


@mcp.tool()
@sdk_tool
def enable_schema_monitoring(
    asset_id: str,
    schedule_type: str = "daily",
    auto_create_baseline: bool = True,
):
    """Enable schema drift monitoring for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        schedule_type: Check schedule ("hourly", "every_4_hours", "daily", "weekly")
        auto_create_baseline: Create baseline if none exists (default True)

    Returns:
        Schema monitoring status with next check time.
    """
    return _get_client().schema.enable_monitoring(
        asset_id=asset_id,
        schedule_type=schedule_type,
        auto_create_baseline=auto_create_baseline,
    )


@mcp.tool()
@sdk_tool
def disable_schema_monitoring(asset_id: str):
    """Disable schema drift monitoring (keeps baseline).

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Confirmation that monitoring is disabled.
    """
    return _get_client().schema.disable_monitoring(asset_id)


# ============================================================================
# Intelligence Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def ask_question(
    asset: str,
    question: str,
    include_related_assets: bool = False,
):
    """Ask a natural language question about your data.

    Uses AnomalyArmor Intelligence to answer questions about database
    structure, lineage, and metadata.

    Args:
        asset: Asset identifier (UUID or qualified name like "postgresql.analytics")
        question: Natural language question (3-2000 chars)
        include_related_assets: Include related assets in context for cross-database queries

    Returns:
        Answer with confidence level, sources used, and token usage.

    Example:
        ask_question("postgresql.analytics", "What tables contain customer data?")
    """
    return _get_client().intelligence.ask(
        asset=asset,
        question=question,
        include_related_assets=include_related_assets,
    )


@mcp.tool()
@sdk_tool
def generate_intelligence(
    asset: str,
    include_schemas: str | None = None,
    force_refresh: bool = False,
):
    """Trigger AI analysis for an asset.

    Generates descriptions, summaries, and knowledge base for Q&A.
    This is an async operation - use job_status() to track progress.

    Args:
        asset: Asset identifier (UUID, short UUID, or name)
        include_schemas: Comma-separated schemas to analyze (None = all)
        force_refresh: Force regeneration even if intelligence exists

    Returns:
        Job with job_id for tracking progress via job_status().
    """
    return _get_client().intelligence.generate(
        asset=asset,
        include_schemas=include_schemas,
        force_refresh=force_refresh,
    )


# ============================================================================
# Lineage Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def get_lineage(
    asset_id: str,
    depth: int = 1,
    direction: str = "both",
):
    """Get lineage graph for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        depth: Levels of lineage to fetch (1-5)
        direction: "upstream" (dependencies), "downstream" (dependents), or "both"

    Returns:
        Lineage graph with root, upstream nodes, downstream nodes, and edges.
    """
    return _get_client().lineage.get(asset_id, depth=depth, direction=direction)


# ============================================================================
# Job Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def job_status(job_id: str):
    """Get status of an async job.

    Use this to track progress of operations like generate_intelligence() or trigger_asset_discovery().

    Args:
        job_id: Job UUID returned from async operations

    Returns:
        Job status with status (pending/running/completed/failed), progress percentage, and error if failed.
    """
    return _get_client().jobs.status(job_id)


# ============================================================================
# Server Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
