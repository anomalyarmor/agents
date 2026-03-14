"""AnomalyArmor MCP Server.

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
# Briefings Tools (TECH-807)
# ============================================================================


@mcp.tool()
@sdk_tool
def get_todays_briefing():
    """Get today's daily briefing digest with key insights and alerts summary.

    Generates the briefing on-demand if it hasn't been created yet today.

    Returns:
        Briefing data including title, sections, and insights.
    """
    return _get_client().briefings.today()


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


@mcp.tool()
@sdk_tool
def list_inbox_alerts(
    state: str | None = None,
    severity: str | None = None,
    event_type: str | None = None,
    limit: int = 25,
):
    """List inbox alerts that can be acknowledged, resolved, or dismissed.

    Unlike list_alerts(), this returns alerts from the inbox that support
    lifecycle actions (acknowledge, resolve, dismiss, snooze).

    Args:
        state: Filter by state ("new", "acknowledged", "resolved", "dismissed")
        severity: Filter by severity ("info", "warning", "critical")
        event_type: Filter by event type (e.g., "freshness_stale", "schema_drift")
        limit: Maximum number of results (default 25, max 100)

    Returns:
        List of inbox alerts with id, title, severity, alert_state, event_type, etc.
    """
    return _get_client().alerts.list_inbox(
        state=state,
        severity=severity,
        event_type=event_type,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def acknowledge_alert(alert_id: str, notes: str | None = None):
    """Acknowledge an alert - mark it as seen/being worked on.

    Args:
        alert_id: Alert public UUID (from list_inbox_alerts)
        notes: Optional notes about the acknowledgment

    Returns:
        Dict with alert id and new status.
    """
    return _get_client().alerts.acknowledge(alert_id, notes=notes)


@mcp.tool()
@sdk_tool
def resolve_alert(
    alert_id: str,
    notes: str | None = None,
    action_category: str | None = None,
    action_detail: str | None = None,
    root_cause_category: str | None = None,
    root_cause_detail: str | None = None,
    pr_url: str | None = None,
    job_run_id: str | None = None,
    external_link: str | None = None,
):
    """Resolve an alert with optional resolution metadata.

    Args:
        alert_id: Alert public UUID (from list_inbox_alerts)
        notes: Optional resolution notes
        action_category: One of: reran_job, updated_sql, rolled_back, contacted_producer,
                         false_positive, expected_behavior, configuration_fix, code_change, other
        action_detail: Details about the action taken
        root_cause_category: One of: pipeline_failure, schema_change, data_source_issue,
                             configuration_error, expected_behavior, code_change, infrastructure, unknown
        root_cause_detail: Details about the root cause
        pr_url: URL to the pull request that fixes this
        job_run_id: ID of the job run related to the fix
        external_link: Link to external tracking system

    Returns:
        Dict with alert id and new status.
    """
    return _get_client().alerts.resolve(
        alert_id,
        notes=notes,
        action_category=action_category,
        action_detail=action_detail,
        root_cause_category=root_cause_category,
        root_cause_detail=root_cause_detail,
        pr_url=pr_url,
        job_run_id=job_run_id,
        external_link=external_link,
    )


@mcp.tool()
@sdk_tool
def dismiss_alert(
    alert_id: str,
    notes: str | None = None,
    action_category: str | None = None,
    action_detail: str | None = None,
    root_cause_category: str | None = None,
    root_cause_detail: str | None = None,
    pr_url: str | None = None,
    job_run_id: str | None = None,
    external_link: str | None = None,
):
    """Dismiss an alert with optional resolution metadata.

    Args:
        alert_id: Alert public UUID (from list_inbox_alerts)
        notes: Optional notes explaining the dismissal
        action_category: One of: reran_job, updated_sql, rolled_back, contacted_producer,
                         false_positive, expected_behavior, configuration_fix, code_change, other
        action_detail: Details about the action taken
        root_cause_category: One of: pipeline_failure, schema_change, data_source_issue,
                             configuration_error, expected_behavior, code_change, infrastructure, unknown
        root_cause_detail: Details about the root cause
        pr_url: URL to the pull request
        job_run_id: ID of the related job run
        external_link: Link to external tracking system

    Returns:
        Dict with alert id and new status.
    """
    return _get_client().alerts.dismiss(
        alert_id,
        notes=notes,
        action_category=action_category,
        action_detail=action_detail,
        root_cause_category=root_cause_category,
        root_cause_detail=root_cause_detail,
        pr_url=pr_url,
        job_run_id=job_run_id,
        external_link=external_link,
    )


@mcp.tool()
@sdk_tool
def snooze_alert(alert_id: str, duration_hours: int, notes: str | None = None):
    """Snooze an alert for a specified duration.

    Args:
        alert_id: Alert public UUID (from list_inbox_alerts)
        duration_hours: Hours to snooze (1-720, max 30 days)
        notes: Optional notes

    Returns:
        Dict with alert id, status, and snoozed_until timestamp.
    """
    return _get_client().alerts.snooze(
        alert_id, duration_hours=duration_hours, notes=notes
    )


# ============================================================================
# Alert Destination Tools (TECH-892)
# ============================================================================


@mcp.tool()
@sdk_tool
def list_destinations(
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    """List configured alert destinations (Slack, webhook, email, PagerDuty, etc).

    Shows where alerts are delivered to.

    Args:
        active_only: Only return active destinations (default False)
        limit: Maximum results (default 50)
        offset: Pagination offset

    Returns:
        List of destinations with id, name, type, active status, and delivery stats.
    """
    return _get_client().alerts.list_destinations(
        active_only=active_only,
        limit=limit,
        offset=offset,
    )


@mcp.tool()
@sdk_tool
def get_destination(destination_id: str):
    """Get details for a specific alert destination.

    Args:
        destination_id: Destination public UUID

    Returns:
        Destination details including name, type, config, and delivery stats.
    """
    return _get_client().alerts.get_destination(destination_id)


@mcp.tool()
@sdk_tool
def create_destination(
    name: str,
    destination_type: str,
    config: dict,
):
    """Create a new alert destination.

    Args:
        name: Destination name (e.g., "Slack #alerts", "PagerDuty Oncall")
        destination_type: Type of destination. One of:
            - email: config = {"email": "user@example.com"} or {"recipients": ["a@b.com"]}
            - slack: config = {"webhook_url": "https://hooks.slack.com/..."}
            - webhook: config = {"url": "https://...", "headers": {...}}
            - teams: config = {"webhook_url": "https://..."}
            - pagerduty: config = {"api_token": "...", "routing_key": "..."}
            - incidentio: config = {"api_key": "...", "severity": "..."}
        config: Configuration dict (varies by destination_type, see above)

    Returns:
        Created destination with id, name, type, and verification status.
    """
    return _get_client().alerts.create_destination(
        name=name,
        destination_type=destination_type,
        config=config,
    )


@mcp.tool()
@sdk_tool
def update_destination(
    destination_id: str,
    name: str | None = None,
    config: dict | None = None,
    is_active: bool | None = None,
):
    """Update an existing alert destination.

    Args:
        destination_id: Destination public UUID
        name: New destination name (optional)
        config: Updated configuration dict (optional)
        is_active: Set active/inactive status (optional)

    Returns:
        Updated destination details.
    """
    kwargs: dict = {}
    for key, val in {
        "name": name,
        "config": config,
        "is_active": is_active,
    }.items():
        if val is not None:
            kwargs[key] = val
    return _get_client().alerts.update_destination(destination_id, **kwargs)


@mcp.tool()
@sdk_tool
def delete_destination(destination_id: str):
    """Delete an alert destination.

    Args:
        destination_id: Destination public UUID

    Returns:
        Confirmation of deletion.
    """
    _get_client().alerts.delete_destination(destination_id)
    return {"deleted": True, "destination_id": destination_id}


@mcp.tool()
@sdk_tool
def test_destination(destination_id: str):
    """Test an alert destination by sending a test notification.

    For email: sends a real test email.
    For Slack: sends a real test message.
    For other types: validates configuration format.

    Args:
        destination_id: Destination public UUID

    Returns:
        Test result with destination_id, test_sent status, and message.
    """
    return _get_client().alerts.test_destination(destination_id)


# ============================================================================
# Alert Rule Tools (TECH-892)
# ============================================================================


@mcp.tool()
@sdk_tool
def list_alert_rules(
    enabled_only: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    """List alert rules that control when and where alerts are sent.

    Args:
        enabled_only: Only return enabled rules (default False)
        limit: Maximum results (default 50)
        offset: Pagination offset

    Returns:
        List of alert rules with id, name, event_types, severities, and destinations.
    """
    return _get_client().alerts.rules(
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )


@mcp.tool()
@sdk_tool
def create_alert_rule(
    name: str,
    destination_ids: list[str],
    description: str | None = None,
    is_active: bool = True,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    tag_filter_mode: str | None = None,
    tag_filter_tags: list[str] | None = None,
    is_notify_code_authors: bool | None = None,
    code_author_min_confidence: float | None = None,
):
    """Create a new alert rule to route alerts to destinations.

    Args:
        name: Rule name (e.g., "Critical Alerts to Slack")
        destination_ids: List of destination UUIDs to send alerts to
        description: Optional rule description
        is_active: Whether the rule is active (default True)
        event_types: Event types to alert on (e.g., ["freshness_alert", "schema_drift",
                     "metric_anomaly", "validity_failure"])
        severities: Severity levels to match (e.g., ["critical", "warning", "info"])
        tag_filter_mode: "any" or "all" for tag-based filtering
        tag_filter_tags: Tags to filter by (used with tag_filter_mode)
        is_notify_code_authors: Notify code authors via git blame (default False)
        code_author_min_confidence: Min git blame confidence 0.0-1.0

    Returns:
        Created alert rule with id, name, and configuration.
    """
    kwargs: dict = {
        "name": name,
        "destination_ids": destination_ids,
        "is_active": is_active,
    }
    for key, val in {
        "description": description,
        "event_types": event_types,
        "severities": severities,
        "tag_filter_mode": tag_filter_mode,
        "tag_filter_tags": tag_filter_tags,
        "is_notify_code_authors": is_notify_code_authors,
        "code_author_min_confidence": code_author_min_confidence,
    }.items():
        if val is not None:
            kwargs[key] = val
    return _get_client().alerts.create_rule(**kwargs)


@mcp.tool()
@sdk_tool
def get_alert_rule(rule_id: str):
    """Get details for a specific alert rule.

    Args:
        rule_id: Rule public UUID

    Returns:
        Alert rule with name, event_types, severities, destinations, and status.
    """
    return _get_client().alerts.get_rule(rule_id)


@mcp.tool()
@sdk_tool
def update_alert_rule(
    rule_id: str,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    destination_ids: list[str] | None = None,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    tag_filter_mode: str | None = None,
    tag_filter_tags: list[str] | None = None,
    is_notify_code_authors: bool | None = None,
    code_author_min_confidence: float | None = None,
):
    """Update an existing alert rule.

    Args:
        rule_id: Rule public UUID
        name: New rule name
        description: Updated description
        is_active: Enable/disable the rule
        destination_ids: Updated list of destination UUIDs to route alerts to
        event_types: Event types to alert on
        severities: Severity levels to match
        tag_filter_mode: "any" or "all" for tag-based filtering
        tag_filter_tags: Tags to filter by
        is_notify_code_authors: Notify code authors via git blame
        code_author_min_confidence: Min git blame confidence 0.0-1.0

    Returns:
        Updated alert rule.
    """
    kwargs: dict = {}
    for key, val in {
        "name": name,
        "description": description,
        "is_active": is_active,
        "destination_ids": destination_ids,
        "event_types": event_types,
        "severities": severities,
        "tag_filter_mode": tag_filter_mode,
        "tag_filter_tags": tag_filter_tags,
        "is_notify_code_authors": is_notify_code_authors,
        "code_author_min_confidence": code_author_min_confidence,
    }.items():
        if val is not None:
            kwargs[key] = val
    return _get_client().alerts.update_rule(rule_id, **kwargs)


@mcp.tool()
@sdk_tool
def delete_alert_rule(rule_id: str):
    """Delete an alert rule.

    Args:
        rule_id: Rule public UUID

    Returns:
        Confirmation of deletion.
    """
    _get_client().alerts.delete_rule(rule_id)
    return {"deleted": True, "rule_id": rule_id}


# ============================================================================
# Alert History & Trends (TECH-892)
# ============================================================================


@mcp.tool()
@sdk_tool
def alert_history(alert_id: str):
    """Get resolution history for a specific alert.

    Shows all actions taken on the alert (acknowledge, resolve, dismiss, snooze).

    Args:
        alert_id: Alert public UUID

    Returns:
        List of history entries with action, timestamp, user_id, and notes.
    """
    return _get_client().alerts.history(alert_id)


@mcp.tool()
@sdk_tool
def alert_trends(period: str = "7d"):
    """Get alert volume trends over time.

    Useful for understanding alert patterns and reducing alert fatigue.

    Args:
        period: Time period - "24h", "7d", "30d", or "90d" (default "7d")

    Returns:
        Trend data with period and time-series data points.
    """
    return _get_client().alerts.trends(period=period)


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
# Metrics Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def list_metrics(
    asset_id: str,
    metric_type: str | None = None,
    limit: int = 50,
):
    """List data quality metrics for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        metric_type: Filter by type (row_count, null_rate, distinct_count, etc.)
        limit: Maximum number of results

    Returns:
        List of metrics with their current status.
    """
    return _get_client().metrics.list(asset_id, metric_type=metric_type, limit=limit)


@mcp.tool()
@sdk_tool
def get_metrics_summary(asset_id: str):
    """Get metrics summary for an asset.

    Returns total counts, passing/failing metrics overview.

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Summary with total_metrics, passing_count, failing_count.
    """
    return _get_client().metrics.summary(asset_id)


@mcp.tool()
@sdk_tool
def create_metric(
    asset_id: str,
    metric_type: str,
    table_path: str,
    column_name: str | None = None,
    capture_interval: str = "daily",
):
    """Create a data quality metric.

    Args:
        asset_id: Asset UUID or qualified name
        metric_type: Type of metric (row_count, null_rate, distinct_count, freshness)
        table_path: Fully qualified table path (e.g., "public.orders")
        column_name: Column name (required for column-level metrics like null_rate)
        capture_interval: How often to capture (daily, hourly, weekly)

    Returns:
        Created metric object with id, name, and status.
    """
    return _get_client().metrics.create(
        asset_id=asset_id,
        metric_type=metric_type,
        table_path=table_path,
        column_name=column_name,
        capture_interval=capture_interval,
    )


@mcp.tool()
@sdk_tool
def delete_metric(asset_id: str, metric_id: str):
    """Delete a metric.

    Args:
        asset_id: Asset UUID or qualified name
        metric_id: Metric UUID to delete

    Returns:
        Confirmation of deletion.
    """
    _get_client().metrics.delete(asset_id, metric_id)
    return {"deleted": True, "metric_id": metric_id}


@mcp.tool()
@sdk_tool
def capture_metric(asset_id: str, metric_id: str):
    """Trigger immediate capture of a metric.

    Args:
        asset_id: Asset UUID or qualified name
        metric_id: Metric UUID to capture

    Returns:
        Capture result with value and timestamp.
    """
    return _get_client().metrics.capture(asset_id, metric_id)


# ============================================================================
# Validity Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def list_validity_rules(
    asset_id: str,
    rule_type: str | None = None,
    limit: int = 50,
):
    """List validity rules for an asset.

    Args:
        asset_id: Asset UUID or qualified name
        rule_type: Filter by type (NOT_NULL, UNIQUE, ACCEPTED_VALUES, REGEX, CUSTOM)
        limit: Maximum number of results

    Returns:
        List of validity rules with their current status.
    """
    return _get_client().validity.list(asset_id, rule_type=rule_type, limit=limit)


@mcp.tool()
@sdk_tool
def get_validity_summary(asset_id: str):
    """Get validity summary for an asset.

    Returns total rules, passing/failing overview.

    Args:
        asset_id: Asset UUID or qualified name

    Returns:
        Summary with total_rules, passing_count, failing_count.
    """
    return _get_client().validity.summary(asset_id)


@mcp.tool()
@sdk_tool
def create_validity_rule(
    asset_id: str,
    rule_type: str,
    table_path: str,
    column_name: str | None = None,
    severity: str = "warning",
):
    """Create a validity rule (data quality check).

    Args:
        asset_id: Asset UUID or qualified name
        rule_type: Type of rule (NOT_NULL, UNIQUE, ACCEPTED_VALUES, REGEX, CUSTOM)
        table_path: Fully qualified table path (e.g., "public.orders")
        column_name: Column name (required for column-level rules)
        severity: Alert severity if rule fails (info, warning, critical)

    Returns:
        Created validity rule with id, name, and status.
    """
    return _get_client().validity.create(
        asset_id=asset_id,
        rule_type=rule_type,
        table_path=table_path,
        column_name=column_name,
        severity=severity,
    )


@mcp.tool()
@sdk_tool
def delete_validity_rule(asset_id: str, rule_id: str):
    """Delete a validity rule.

    Args:
        asset_id: Asset UUID or qualified name
        rule_id: Rule UUID to delete

    Returns:
        Confirmation of deletion.
    """
    _get_client().validity.delete(asset_id, rule_id)
    return {"deleted": True, "rule_id": rule_id}


@mcp.tool()
@sdk_tool
def check_validity_rule(asset_id: str, rule_id: str):
    """Run a validity check immediately.

    Args:
        asset_id: Asset UUID or qualified name
        rule_id: Rule UUID to check

    Returns:
        Check result with status (passing/failing) and details.
    """
    return _get_client().validity.check(asset_id, rule_id)


# ============================================================================
# Tags Tools
# ============================================================================


@mcp.tool()
@sdk_tool
def list_tags(
    asset: str,
    category: str | None = None,
    limit: int = 100,
):
    """List tags for an asset.

    Args:
        asset: Asset UUID or qualified name (e.g., "postgresql.analytics")
        category: Filter by category (business, technical, governance)
        limit: Maximum number of results

    Returns:
        List of tags with name, category, and object_path.
    """
    return _get_client().tags.list(asset=asset, category=category, limit=limit)


@mcp.tool()
@sdk_tool
def create_tag(
    asset: str,
    name: str,
    object_path: str,
    object_type: str = "table",
    category: str = "business",
    description: str | None = None,
):
    """Create a tag on a database object.

    Args:
        asset: Asset UUID or qualified name
        name: Tag name (e.g., "pii_data", "financial_reporting")
        object_path: Path to object (e.g., "schema.table" or "schema.table.column")
        object_type: Type of object: "table" or "column"
        category: Tag category: "business", "technical", or "governance"
        description: Optional tag description

    Returns:
        Created tag with id, name, and category.
    """
    return _get_client().tags.create(
        asset=asset,
        name=name,
        object_path=object_path,
        object_type=object_type,
        category=category,
        description=description,
    )


@mcp.tool()
@sdk_tool
def apply_tags(
    asset: str,
    tag_names: list[str],
    object_paths: list[str],
    category: str = "business",
):
    """Apply multiple tags to multiple objects within an asset.

    Args:
        asset: Asset UUID or qualified name
        tag_names: List of tag names to apply
        object_paths: List of object paths to tag
        category: Tag category for all tags

    Returns:
        Result with applied and failed counts.
    """
    return _get_client().tags.apply(
        asset=asset,
        tag_names=tag_names,
        object_paths=object_paths,
        category=category,
    )


@mcp.tool()
@sdk_tool
def bulk_apply_tag(
    tag_name: str,
    asset_ids: list[str],
    category: str = "business",
):
    """Apply a tag to multiple assets.

    Args:
        tag_name: Tag name to apply
        asset_ids: List of asset UUIDs or qualified names
        category: Tag category

    Returns:
        Result with applied and failed counts.
    """
    return _get_client().tags.bulk_apply(
        tag_name=tag_name,
        asset_ids=asset_ids,
        category=category,
    )


# ============================================================================
# Dry-Run / Preview Tools (TECH-771)
# ============================================================================


@mcp.tool()
@sdk_tool
def dry_run_freshness(
    asset_id: str,
    table_path: str,
    expected_interval_hours: float,
    lookback_days: int = 7,
):
    """Dry-run a freshness threshold to see what alerts would fire.

    Uses historical data to predict alert frequency before enabling monitoring.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.orders")
        expected_interval_hours: Proposed threshold in hours
        lookback_days: Historical period to analyze (default 7)

    Returns:
        total_checks: Number of data points analyzed
        would_alert_count: Times threshold would have fired
        alert_rate_percent: Percentage of checks that would alert
        current_age_hours: Current data age
        would_alert_now: Whether this would alert right now
        sample_alerts: Sample of times threshold would have fired
        recommendation: Human-readable recommendation
    """
    return _get_client().freshness.dry_run(
        asset_id=asset_id,
        table_path=table_path,
        expected_interval_hours=expected_interval_hours,
        lookback_days=lookback_days,
    )


@mcp.tool()
@sdk_tool
def dry_run_schema(
    asset_id: str,
    table_path: str | None = None,
    lookback_days: int = 30,
):
    """Dry-run schema drift detection settings.

    Tests what schema changes would be detected with proposed settings.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Filter to specific table (optional)
        lookback_days: Days of history to analyze (default 30)

    Returns:
        total_changes: Total schema changes detected
        changes_summary: Breakdown by change type (dict)
        sample_changes: Sample of detected changes
        recommendation: Human-readable recommendation
    """
    return _get_client().schema.dry_run(
        asset_id=asset_id,
        table_path=table_path,
        lookback_days=lookback_days,
    )


@mcp.tool()
@sdk_tool
def preview_alerts(
    rule_id: str | None = None,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    lookback_days: int = 7,
):
    """Preview what alerts would match a rule configuration.

    Shows how many alerts would fire based on historical data.

    Args:
        rule_id: Existing rule UUID to preview (optional)
        event_types: Event types to match (e.g., ["freshness_stale", "schema_drift"])
        severities: Severities to match (e.g., ["critical", "warning"])
        lookback_days: Days of alert history to analyze (default 7)

    Returns:
        alerts_would_match: Number of historical alerts matching
        alerts_by_type: Breakdown by event type (dict)
        alerts_by_severity: Breakdown by severity (dict)
        sample_alerts: Sample of matching alerts
    """
    return _get_client().alerts.preview(
        rule_id=rule_id,
        event_types=event_types,
        severities=severities,
        lookback_days=lookback_days,
    )


@mcp.tool()
@sdk_tool
def dry_run_metric(
    asset_id: str,
    table_path: str,
    metric_type: str,
    column_name: str | None = None,
    sensitivity: float = 1.0,
    lookback_days: int = 30,
):
    """Dry-run a metric threshold to see what alerts would fire.

    Tests a metric against historical values.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Table path (e.g., "public.orders")
        metric_type: Type of metric (null_percent, unique_count, row_count, etc.)
        column_name: Column for column-level metrics (optional)
        sensitivity: Sensitivity multiplier for anomaly detection
        lookback_days: Historical period to analyze (default 30)

    Returns:
        total_snapshots: Data points analyzed
        would_alert_count: Times threshold would have fired
        alert_rate_percent: Percentage of checks that would alert
        recommendation: Human-readable recommendation
    """
    return _get_client().metrics.dry_run(
        asset_id=asset_id,
        table_path=table_path,
        metric_type=metric_type,
        column_name=column_name,
        sensitivity=sensitivity,
        lookback_days=lookback_days,
    )


# ============================================================================
# Recommendation Tools (TECH-772)
# ============================================================================


@mcp.tool()
@sdk_tool
def recommend_freshness(
    asset_id: str,
    min_confidence: float = 0.5,
    limit: int = 20,
    include_monitored: bool = False,
):
    """Get AI-driven recommendations for freshness monitoring.

    Analyzes update patterns to suggest tables and thresholds for freshness monitoring.

    Args:
        asset_id: Asset UUID or qualified name
        min_confidence: Minimum confidence threshold (0.0-1.0, default 0.5)
        limit: Maximum recommendations to return (default 20)
        include_monitored: Include already-monitored tables (default False)

    Returns:
        recommendations: List of table recommendations with:
            - table_path: Table identifier
            - suggested_check_interval: e.g., "1h", "24h"
            - suggested_threshold_hours: Staleness threshold
            - detected_frequency: "hourly", "daily", "weekly", "irregular"
            - confidence: 0.0-1.0
            - reasoning: Human-readable explanation
            - data_points: Number of history entries analyzed
        tables_analyzed: Total tables analyzed
        tables_with_recommendations: Tables with high-confidence recommendations
    """
    return _get_client().recommendations.freshness(
        asset_id=asset_id,
        min_confidence=min_confidence,
        limit=limit,
        include_monitored=include_monitored,
    )


@mcp.tool()
@sdk_tool
def recommend_metrics(
    asset_id: str,
    table_path: str | None = None,
    min_confidence: float = 0.5,
    limit: int = 50,
):
    """Get AI-driven recommendations for data quality metrics.

    Analyzes column types and naming patterns to suggest quality checks.

    Args:
        asset_id: Asset UUID or qualified name
        table_path: Specific table to analyze (optional, None = all tables)
        min_confidence: Minimum confidence threshold (0.0-1.0, default 0.5)
        limit: Maximum recommendations to return (default 50)

    Returns:
        recommendations: List of metric recommendations with:
            - table_path: Table identifier
            - column_name: Column identifier
            - suggested_metric_type: "referential_integrity", "null_rate", etc.
            - reasoning: Why this metric makes sense
            - confidence: 0.0-1.0
        columns_analyzed: Total columns analyzed
        columns_with_recommendations: Columns with recommendations
    """
    return _get_client().recommendations.metrics(
        asset_id=asset_id,
        table_path=table_path,
        min_confidence=min_confidence,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def get_coverage_recommendations(
    asset_id: str,
    limit: int = 20,
):
    """Analyze monitoring coverage and identify gaps.

    Identifies high-value unmonitored tables prioritized by importance.

    Args:
        asset_id: Asset UUID or qualified name
        limit: Maximum recommendations to return (default 20)

    Returns:
        total_tables: Total tables in asset
        monitored_tables: Currently monitored count
        coverage_percentage: Monitoring coverage (0-100)
        recommendations: Prioritized list of unmonitored tables with:
            - table_path: Table identifier
            - importance_score: 0.0-1.0
            - row_count: Estimated rows
            - reasoning: Why this table is important
    """
    return _get_client().recommendations.coverage(
        asset_id=asset_id,
        limit=limit,
    )


@mcp.tool()
@sdk_tool
def recommend_thresholds(
    asset_id: str,
    days: int = 30,
    limit: int = 10,
):
    """Get threshold adjustment suggestions to reduce alert fatigue.

    Analyzes historical alerts to suggest threshold tuning.

    Args:
        asset_id: Asset UUID or qualified name
        days: Historical window for analysis (default 30)
        limit: Maximum recommendations to return (default 10)

    Returns:
        recommendations: List of threshold adjustments with:
            - table_path: Table identifier
            - current_threshold: Current setting
            - suggested_threshold: Recommended adjustment
            - direction: "increase" or "decrease"
            - reasoning: Why this change
            - confidence: 0.0-1.0
            - historical_alerts: Alert count in period
            - projected_reduction: Estimated alert reduction
        monitored_items_analyzed: Items analyzed
        items_with_recommendations: Items needing adjustment
    """
    return _get_client().recommendations.thresholds(
        asset_id=asset_id,
        days=days,
        limit=limit,
    )


# ============================================================================
# Coverage Tools
# ============================================================================


@mcp.tool()
def get_coverage_summary():
    """Get monitoring coverage summary across all assets.

    Analyzes what percentage of assets have:
    - Freshness monitoring
    - Health status

    Returns:
        Coverage summary with total_assets, freshness_monitored, and health status.
    """
    try:
        client = _get_client()

        # Get all assets
        assets = client.assets.list(limit=100)
        total_assets = len(assets)

        # Get freshness schedules
        freshness_error = None
        try:
            freshness_schedules = client.freshness.list_schedules(limit=100)
            freshness_monitored = len(
                set(
                    s.asset_id
                    for s in freshness_schedules
                    if hasattr(s, "asset_id") and s.asset_id
                )
            )
        except Exception as e:
            freshness_monitored = None
            freshness_error = f"Could not fetch freshness schedules: {e}"

        # Get health summary for overall status
        try:
            health = client.health.summary()
            health_data = (
                health.model_dump() if hasattr(health, "model_dump") else str(health)
            )
        except Exception:
            health_data = {"error": "Could not fetch health summary"}

        result = {
            "total_assets": total_assets,
            "freshness_monitored": freshness_monitored,
            "freshness_coverage_percent": (
                round(100 * freshness_monitored / total_assets)
                if total_assets > 0 and freshness_monitored is not None
                else None
            ),
            "health_status": health_data,
        }

        if freshness_error:
            result["freshness_error"] = freshness_error

        return result
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


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
    """Create Clerk OAuth auth provider for HTTP mode.

    Uses FastMCP's built-in JWTVerifier for RS256 JWKS validation
    and RemoteAuthProvider for RFC 9728 .well-known metadata.

    Returns:
        RemoteAuthProvider configured for Clerk, or None if CLERK_DOMAIN not set.
    """
    clerk_domain = os.environ.get("CLERK_DOMAIN", "")
    if not clerk_domain:
        return None

    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider

    base_url = os.environ.get("MCP_BASE_URL", "https://mcp.anomalyarmor.ai")

    token_verifier = JWTVerifier(
        jwks_uri=f"https://{clerk_domain}/.well-known/jwks.json",
        issuer=f"https://{clerk_domain}",
        audience=None,  # Clerk doesn't set aud on OAuth tokens
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
    """Run the MCP server.

    Transport mode is determined by MCP_TRANSPORT env var:
    - "stdio" (default): Standard MCP stdio transport with API key auth
    - "http": Streamable HTTP transport with Clerk OAuth 2.1
    """
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
