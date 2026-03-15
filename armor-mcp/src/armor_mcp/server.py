"""AnomalyArmor MCP Server.

TECH-904: Consolidated from 74 tools to ~30 intent-based tools.

This module provides an MCP server that wraps the AnomalyArmor Python SDK,
exposing data observability tools to AI assistants like Claude Code and Cursor.

Supports two transport modes:
    - stdio (default): API key auth via ARMOR_API_KEY env var
    - HTTP: Clerk OAuth 2.1 via FastMCP's built-in JWTVerifier + RemoteAuthProvider

Usage:
    # Stdio mode (default)
    uvx armor-mcp

    # HTTP mode with Clerk OAuth
    MCP_TRANSPORT=http CLERK_DOMAIN=clerk.example.com uvx armor-mcp
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, TypeVar

from fastmcp import FastMCP

mcp = FastMCP("armor-mcp", instructions="AnomalyArmor Data Observability Tools")

T = TypeVar("T")

# Singleton client instance (stdio mode only)
_client: Any = None


def _get_client() -> Any:
    """Get SDK client for the current request.

    In HTTP mode: creates a per-request client using the Clerk JWT from
    FastMCP's auth context (token passthrough to backend).
    In stdio mode: returns a singleton client using ARMOR_API_KEY from env.

    Returns:
        Initialized AnomalyArmor Client instance.

    Raises:
        RuntimeError: If SDK is not installed or auth is not configured.
    """
    try:
        from anomalyarmor import Client
        from anomalyarmor.exceptions import AuthenticationError
    except ImportError as e:
        raise RuntimeError(
            "anomalyarmor SDK not installed. Run: pip install anomalyarmor"
        ) from e

    # HTTP mode: per-request client with Clerk JWT as Bearer token
    try:
        from fastmcp.server.dependencies import get_access_token

        token = get_access_token()
        if token is not None:
            return Client(api_key=token.token)
    except (ImportError, RuntimeError):
        # ImportError: fastmcp.server.dependencies not available
        # RuntimeError: get_access_token() called outside HTTP request context
        pass

    # Stdio mode: singleton client with API key from env
    global _client
    if _client is None:
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
# Health & Discovery
# ============================================================================


@mcp.tool()
@sdk_tool
def health_summary():
    """Get overall health status of monitored data assets.

    Returns aggregated status across alerts, freshness, schema drift,
    metrics, and validity. Use this as the first call when checking
    "is my data healthy?"
    """
    return _get_client().health.summary()


@mcp.tool()
@sdk_tool
def list_assets(
    asset_type: str | None = None,
    limit: int = 25,
):
    """List connected data sources (databases, warehouses).

    Args:
        asset_type: Filter by type ("postgresql", "snowflake", "bigquery", etc.)
        limit: Maximum results (default 25)
    """
    return _get_client().assets.list(asset_type=asset_type, limit=limit)


@mcp.tool()
@sdk_tool
def trigger_asset_discovery(asset_id: str):
    """Start schema discovery for an asset. Discovers all schemas, tables,
    columns, and metadata. Runs as background job - use job_status() to track.

    Args:
        asset_id: Asset UUID or qualified name
    """
    return _get_client().assets.trigger_discovery(asset_id)


# ============================================================================
# Freshness Monitoring
# ============================================================================


@mcp.tool()
@sdk_tool
def get_freshness_summary():
    """Get freshness monitoring summary across all assets.

    Returns counts of fresh, stale, unknown, and disabled tables,
    plus overall freshness rate.
    """
    return _get_client().freshness.summary()


@mcp.tool()
@sdk_tool
def check_freshness(asset_id: str):
    """Check freshness status for a specific asset's tables.

    Args:
        asset_id: Asset UUID or qualified name
    """
    return _get_client().freshness.check(asset_id)


@mcp.tool()
@sdk_tool
def setup_freshness(
    asset_id: str,
    table_path: str,
    check_interval: str = "1h",
    expected_interval_hours: float | None = None,
    freshness_column: str | None = None,
    monitoring_mode: str = "auto_learn",
):
    """Set up freshness monitoring for a table.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.orders")
        check_interval: Check frequency ("5m", "1h", "6h", "1d", "1w")
        expected_interval_hours: Hours until stale (required for explicit mode)
        freshness_column: Column to check (auto-detected if not provided)
        monitoring_mode: "auto_learn" (recommended) or "explicit"
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
def list_freshness_schedules(
    asset_id: str | None = None,
    limit: int = 25,
):
    """List freshness monitoring schedules.

    Args:
        asset_id: Filter by asset UUID or qualified name
        limit: Maximum results (default 25)
    """
    return _get_client().freshness.list_schedules(asset_id=asset_id, limit=limit)


# ============================================================================
# Schema Monitoring
# ============================================================================


@mcp.tool()
@sdk_tool
def get_schema_summary():
    """Get schema drift summary across all assets.

    Returns counts of total changes, unacknowledged changes,
    and severity breakdown.
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
    """Capture current schema as baseline for drift detection.

    Args:
        asset_id: Asset UUID or qualified name
        description: Optional description for the baseline
    """
    return _get_client().schema.create_baseline(asset_id, description=description)


@mcp.tool()
@sdk_tool
def enable_schema_monitoring(
    asset_id: str,
    schedule_type: str = "1d",
    auto_create_baseline: bool = True,
):
    """Enable schema drift monitoring for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        schedule_type: Check interval ("5m", "1h", "6h", "1d", "1w",
                       or legacy: "hourly", "daily", "weekly")
        auto_create_baseline: Create baseline if none exists (default True)
    """
    return _get_client().schema.enable_monitoring(
        asset_id=asset_id,
        schedule_type=schedule_type,
        auto_create_baseline=auto_create_baseline,
    )


@mcp.tool()
@sdk_tool
def disable_schema_monitoring(asset_id: str):
    """Disable schema drift monitoring for an asset (keeps baseline).

    Args:
        asset_id: Asset UUID or qualified name
    """
    return _get_client().schema.disable_monitoring(asset_id)


@mcp.tool()
@sdk_tool
def dry_run_schema(asset_id: str, schedule_type: str = "1d"):
    """Preview schema drift detection without persisting. Compares current
    schema against baseline to show what changes would be detected.

    Args:
        asset_id: Asset UUID or qualified name
        schedule_type: Schedule for alert estimation ("1h", "1d", "1w")
    """
    return _get_client().schema.dry_run(
        asset_id=asset_id, schedule_type=schedule_type,
    )


# ============================================================================
# Data Quality: Metrics
# ============================================================================


@mcp.tool()
@sdk_tool
def list_metrics(asset_id: str, limit: int = 25):
    """List data quality metrics configured for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        limit: Maximum results (default 25)
    """
    return _get_client().metrics.list(asset_id=asset_id, limit=limit)


@mcp.tool()
@sdk_tool
def create_metric(
    asset_id: str,
    table_path: str,
    metric_type: str,
    column_name: str | None = None,
):
    """Create a data quality metric.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.orders")
        metric_type: "row_count", "null_rate", "unique_rate", "min", "max", "mean", "stddev"
        column_name: Column name (required for column-level metrics)
    """
    return _get_client().metrics.create(
        asset_id=asset_id,
        table_path=table_path,
        metric_type=metric_type,
        column_name=column_name,
    )


# ============================================================================
# Data Quality: Validity Rules
# ============================================================================


@mcp.tool()
@sdk_tool
def list_validity_rules(asset_id: str, limit: int = 25):
    """List data validity rules configured for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        limit: Maximum results (default 25)
    """
    return _get_client().validity.list_rules(asset_id=asset_id, limit=limit)


@mcp.tool()
@sdk_tool
def create_validity_rule(
    asset_id: str,
    table_path: str,
    column_name: str,
    rule_type: str,
    rule_config: dict,
    name: str | None = None,
    severity: str = "error",
):
    """Create a data validity rule for a column.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.users")
        column_name: Column to validate
        rule_type: "regex_match", "allowed_values", "range_bounds", "format", "length_bounds"
        rule_config: Config dict, e.g. {"pattern": "^[A-Z]"} for regex_match
        name: Optional rule name
        severity: "error" (default) or "warning"
    """
    return _get_client().validity.create_rule(
        asset_id=asset_id,
        table_path=table_path,
        column_name=column_name,
        rule_type=rule_type,
        rule_config=rule_config,
        name=name,
        severity=severity,
    )


# ============================================================================
# Alerts
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
        from_date: Start of date range (ISO 8601, e.g., "2026-01-29T00:00:00Z")
        to_date: End of date range (ISO 8601)
        limit: Maximum results (default 25, max 100)
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
def update_alert(
    alert_id: str,
    status: str,
    notes: str | None = None,
    duration_hours: int = 24,
    action_category: str | None = None,
    root_cause_category: str | None = None,
):
    """Update alert status: acknowledge, resolve, dismiss, or snooze.

    Args:
        alert_id: Alert public UUID (from list_alerts)
        status: "acknowledged", "resolved", "dismissed", or "snoozed"
        notes: Optional notes about the action
        duration_hours: Hours to snooze (only for status="snoozed", default 24)
        action_category: For resolve/dismiss: reran_job, updated_sql, rolled_back,
                         false_positive, expected_behavior, code_change, other
        root_cause_category: For resolve/dismiss: pipeline_failure, schema_change,
                            data_source_issue, configuration_error, expected_behavior,
                            code_change, infrastructure, unknown
    """
    valid_statuses = ("acknowledged", "resolved", "dismissed", "snoozed")
    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Must be: acknowledged, resolved, dismissed, or snoozed"
        )

    client = _get_client()
    if status == "acknowledged":
        return client.alerts.acknowledge(alert_id, notes=notes)
    elif status == "resolved":
        return client.alerts.resolve(
            alert_id, notes=notes,
            action_category=action_category,
            root_cause_category=root_cause_category,
        )
    elif status == "dismissed":
        return client.alerts.dismiss(
            alert_id, notes=notes,
            action_category=action_category,
            root_cause_category=root_cause_category,
        )
    elif status == "snoozed":
        return client.alerts.snooze(
            alert_id, duration_hours=duration_hours, notes=notes,
        )


@mcp.tool()
@sdk_tool
def list_alert_rules(
    asset_id: str | None = None,
    active_only: bool = True,
):
    """List configured alert rules.

    Args:
        asset_id: Filter by asset UUID or qualified name
        active_only: Only return active rules (default True)
    """
    return _get_client().alerts.list_rules(
        asset_id=asset_id, active_only=active_only,
    )


@mcp.tool()
@sdk_tool
def create_alert_rule(
    name: str,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    description: str | None = None,
    destination_ids: list[str] | None = None,
    asset_ids: list[str] | None = None,
):
    """Create an alert routing rule.

    Args:
        name: Rule name
        event_types: Event types to match (e.g., ["freshness_stale", "schema_drift"])
        severities: Severity levels (e.g., ["warning", "critical"])
        description: Optional description
        destination_ids: Alert destination UUIDs to notify (from list_destinations)
        asset_ids: Asset UUIDs to scope the rule to
    """
    return _get_client().alerts.create_rule(
        name=name,
        event_types=event_types,
        severities=severities,
        description=description,
        destination_ids=destination_ids,
        asset_ids=asset_ids,
    )


# ============================================================================
# Destinations
# ============================================================================


@mcp.tool()
@sdk_tool
def list_destinations(
    destination_type: str | None = None,
    active_only: bool = True,
):
    """List configured alert destinations.

    Args:
        destination_type: Filter by type ("slack", "webhook", "email")
        active_only: Only return active destinations (default True)
    """
    return _get_client().destinations.list(
        destination_type=destination_type, active_only=active_only,
    )


@mcp.tool()
@sdk_tool
def setup_destination(
    destination_type: str,
    name: str | None = None,
    channel_name: str | None = None,
    webhook_url: str | None = None,
    email: str | None = None,
):
    """Create an alert destination with smart auto-discovery.

    For Slack: provide channel_name, auto-discovers OAuth connection.
    For webhook: provide webhook_url.
    For email: provide email address.

    Args:
        destination_type: "slack", "webhook", or "email"
        name: Destination name (auto-generated if not provided)
        channel_name: Slack channel name (for type="slack")
        webhook_url: Webhook URL (for type="webhook")
        email: Email address (for type="email")
    """
    if destination_type not in ("slack", "webhook", "email"):
        raise ValueError(f"Unknown type '{destination_type}'. Use slack, webhook, or email.")

    if destination_type == "slack" and not channel_name:
        raise ValueError("channel_name is required for Slack destinations")
    if destination_type == "webhook" and not webhook_url:
        raise ValueError("webhook_url is required for webhook destinations")
    if destination_type == "email" and not email:
        raise ValueError("email is required for email destinations")

    client = _get_client()

    if destination_type == "slack":

        # Auto-discover Slack OAuth connection
        try:
            connections = client.integrations.list_slack_connections()
        except Exception:
            connections = []

        if not connections:
            try:
                oauth = client.integrations.get_slack_oauth_url()
                oauth_url = oauth.url if hasattr(oauth, "url") else str(oauth)
            except Exception:
                oauth_url = "Connect Slack via the AnomalyArmor dashboard"
            return {
                "error": "No Slack workspace connected",
                "oauth_url": oauth_url,
                "message": "Connect your Slack workspace first, then retry.",
            }

        connection = connections[0]
        conn_id = connection.id if hasattr(connection, "id") else connection.get("id")

        # Find channel by name
        try:
            channels = client.integrations.get_slack_channels(conn_id)
        except Exception:
            return {"error": "SlackError", "message": f"Could not list channels for connection {conn_id}"}

        match = None
        close_matches = []
        for ch in channels:
            ch_name = ch.name if hasattr(ch, "name") else ch.get("name", "")
            ch_id = ch.id if hasattr(ch, "id") else ch.get("id", "")
            if ch_name == channel_name:
                match = (ch_id, ch_name)
                break
            if channel_name in ch_name:
                close_matches.append(ch_name)

        if not match:
            msg = f"Channel '#{channel_name}' not found."
            if close_matches:
                msg += f" Similar: {', '.join(close_matches[:5])}"
            return {"error": "NotFoundError", "message": msg}

        channel_id, resolved_name = match
        return client.integrations.create_slack_destination(
            connection_id=conn_id,
            channel_id=channel_id,
            channel_name=resolved_name,
            name=name or f"Slack #{resolved_name}",
        )

    elif destination_type == "webhook":
        return client.destinations.create(
            destination_type="webhook",
            name=name or "Webhook",
            config={"webhook_url": webhook_url},
        )

    elif destination_type == "email":
        return client.destinations.create(
            destination_type="email",
            name=name or f"Email: {email}",
            config={"email": email},
        )


# ============================================================================
# Intelligence
# ============================================================================


@mcp.tool()
@sdk_tool
def ask_question(
    question: str,
    asset_id: str | None = None,
    include_schema: bool = True,
    include_lineage: bool = False,
):
    """Ask a natural language question about your data.

    Args:
        question: Natural language question (e.g., "What tables contain customer PII?")
        asset_id: Optional asset UUID to scope the question
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

    Args:
        asset_id: Asset UUID or qualified name
        force_refresh: Force regeneration even if cached (default False)
    """
    return _get_client().intelligence.generate(
        asset_id=asset_id, force_refresh=force_refresh,
    )


# ============================================================================
# Lineage
# ============================================================================


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


# ============================================================================
# Jobs
# ============================================================================


@mcp.tool()
@sdk_tool
def job_status(job_id: str):
    """Check status of an async job (discovery, intelligence generation, etc.).

    Args:
        job_id: Job UUID (from trigger_asset_discovery, generate_intelligence, etc.)
    """
    return _get_client().jobs.get(job_id)


# ============================================================================
# Tags
# ============================================================================


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


# ============================================================================
# HTTP Health Check
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Any) -> Any:
    """Health check endpoint for load balancer."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "service": "armor-mcp"})


# ============================================================================
# Auth Provider (HTTP mode only)
# ============================================================================


def _create_auth_provider() -> Any:
    """Create Clerk OAuth auth provider for HTTP mode."""
    clerk_domain = os.environ.get("CLERK_DOMAIN", "")
    if not clerk_domain:
        return None

    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider

    base_url = os.environ.get("MCP_BASE_URL", "https://mcp.anomalyarmor.ai")

    token_verifier = JWTVerifier(
        jwks_uri=f"https://{clerk_domain}/.well-known/jwks.json",
        issuer=f"https://{clerk_domain}",
        audience=None,
        algorithm="RS256",
    )

    return RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[f"https://{clerk_domain}"],
        base_url=base_url,
        resource_name="AnomalyArmor MCP Server",
    )


# ============================================================================
# Server Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        auth = _create_auth_provider()
        if auth is None:
            raise RuntimeError(
                "CLERK_DOMAIN is required for HTTP mode. "
                "Set CLERK_DOMAIN env var (e.g., clerk.anomalyarmor.ai)."
            )
        mcp.auth = auth
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "3001")),
            stateless_http=True,
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
