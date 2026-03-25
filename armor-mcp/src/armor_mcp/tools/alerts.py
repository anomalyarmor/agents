"""Alert management tools."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def get_alerts_summary():
    """Get alert overview with counts by status and severity.

    Quick snapshot of triggered, acknowledged, and resolved alerts.
    For individual alerts use list_alerts.
    """
    client = _get_client()
    return await asyncio.to_thread(client.alerts.summary)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    asset_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 25,
):
    """List recent alerts with severity, status, and asset info.

    Use update_alert to acknowledge, resolve, dismiss, or snooze alerts.

    Args:
        status: Filter by status ("triggered", "acknowledged", "resolved", "dismissed", "snoozed")
        severity: Filter by severity ("info", "warning", "critical")
        asset_id: Filter by asset UUID (from list_assets)
        from_date: Start of date range (ISO 8601, e.g., "2026-01-29T00:00:00Z")
        to_date: End of date range (ISO 8601)
        limit: Maximum results (default 25, max 100)
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.alerts.list,
        status=status,
        severity=severity,
        asset_id=asset_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def list_inbox_alerts(
    severity: str | None = None,
    asset_id: str | None = None,
    limit: int = 25,
):
    """List unresolved alerts in inbox view (triggered + acknowledged only).

    Focused view for triaging active alerts. Use update_alert to take action.

    Args:
        severity: Filter by severity ("info", "warning", "critical")
        asset_id: Filter by asset UUID (from list_assets)
        limit: Maximum results (default 25)
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.alerts.list_inbox,
        severity=severity,
        asset_id=asset_id,
        limit=limit,
    )


_VALID_ALERT_STATUSES = ("acknowledged", "resolved", "dismissed", "snoozed")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"alerts", "write"})
@sdk_tool
async def update_alert(
    alert_id: str,
    status: str,
    notes: str | None = None,
    duration_hours: int = 24,
    action_category: str | None = None,
    root_cause_category: str | None = None,
):
    """Update an alert's lifecycle status. Use list_alerts to find alert IDs.

    Args:
        alert_id: Alert UUID (from list_alerts)
        status: New status: "acknowledged", "resolved", "dismissed", or "snoozed"
        notes: Optional notes explaining the status change
        duration_hours: Snooze duration in hours, 1-720 (default 24). Only for status="snoozed".
        action_category: For resolve/dismiss: reran_job, updated_sql, rolled_back,
                         false_positive, expected_behavior, code_change, other
        root_cause_category: For resolve/dismiss: pipeline_failure, schema_change,
                            data_source_issue, configuration_error, expected_behavior,
                            code_change, infrastructure, unknown
    """
    if status not in _VALID_ALERT_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Must be: {', '.join(_VALID_ALERT_STATUSES)}"
        )

    client = _get_client()
    if status == "acknowledged":
        return await asyncio.to_thread(client.alerts.acknowledge, alert_id, notes=notes)
    elif status == "resolved":
        return await asyncio.to_thread(
            client.alerts.resolve,
            alert_id,
            notes=notes,
            action_category=action_category,
            root_cause_category=root_cause_category,
        )
    elif status == "dismissed":
        return await asyncio.to_thread(
            client.alerts.dismiss,
            alert_id,
            notes=notes,
            action_category=action_category,
            root_cause_category=root_cause_category,
        )
    elif status == "snoozed":
        return await asyncio.to_thread(
            client.alerts.snooze,
            alert_id,
            duration_hours=duration_hours,
            notes=notes,
        )
    else:
        raise ValueError(
            f"Unhandled status '{status}', update dispatch to match _VALID_ALERT_STATUSES"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def list_alert_rules(
    asset_id: str | None = None,
    active_only: bool = True,
):
    """List configured alert rules showing which events and severities each rule monitors.

    Use create_alert_rule to add new rules, list_destinations to find
    destination IDs for routing.

    Args:
        asset_id: Filter by asset UUID (from list_assets)
        active_only: Only return active rules (default True)
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.alerts.list_rules,
        asset_id=asset_id,
        active_only=active_only,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False), tags={"alerts", "write"})
@sdk_tool
async def create_alert_rule(
    name: str,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    description: str | None = None,
    destination_ids: list[str] | None = None,
    asset_ids: list[str] | None = None,
):
    """Create an alert rule to notify when data issues are detected.

    Routes to specified destinations (or default email). Use list_destinations
    to find destination IDs, list_assets for asset IDs.

    Args:
        name: Human-readable name for the alert rule
        event_types: Event types to monitor: "freshness_stale", "schema_drift",
                     "metric_anomaly", "validity_failure", "custom_sql". Omit for all.
        severities: Severity levels to trigger on: "info", "warning", "critical". Omit for all.
        description: Optional description of the rule's purpose
        destination_ids: UUIDs of destinations to route alerts to (from list_destinations).
                         Falls back to default email if omitted.
        asset_ids: UUIDs of assets to scope the rule to (from list_assets). Omit for all.
    """
    client = _get_client()
    return await asyncio.to_thread(
        client.alerts.create_rule,
        name=name,
        event_types=event_types,
        severities=severities,
        description=description,
        destination_ids=destination_ids,
        asset_ids=asset_ids,
    )


_VALID_RULE_ACTIONS = ("get", "update", "delete")


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True), tags={"alerts", "delete"})
@sdk_tool
async def manage_alert_rule(
    action: str,
    rule_id: str,
    name: str | None = None,
    event_types: list[str] | None = None,
    severities: list[str] | None = None,
    description: str | None = None,
    is_active: bool | None = None,
):
    """Manage an existing alert rule: get details, update, or delete.

    Use list_alert_rules to find rule IDs.

    Args:
        action: Operation: "get", "update", or "delete"
        rule_id: Alert rule UUID (from list_alert_rules)
        name: New name (for update)
        event_types: New event types (for update)
        severities: New severity levels (for update)
        description: New description (for update)
        is_active: Enable/disable rule (for update)
    """
    if action not in _VALID_RULE_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. " f"Must be: {', '.join(_VALID_RULE_ACTIONS)}"
        )

    client = _get_client()

    if action == "get":
        return await asyncio.to_thread(client.alerts.get_rule, rule_id)
    elif action == "update":
        return await asyncio.to_thread(
            client.alerts.update_rule,
            rule_id=rule_id,
            name=name,
            event_types=event_types,
            severities=severities,
            description=description,
            is_active=is_active,
        )
    elif action == "delete":
        return await asyncio.to_thread(client.alerts.delete_rule, rule_id)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_RULE_ACTIONS"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def get_alert_trends(period: str = "7d"):
    """Get aggregate alert trend data across all assets.

    Shows alert volume and patterns over time for trend analysis.

    Args:
        period: Time period: "24h", "7d", "30d", "90d" (default "7d")
    """
    client = _get_client()
    return await asyncio.to_thread(client.alerts.trends, period=period)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True), tags={"alerts", "read"})
@sdk_tool
async def get_alert_history(alert_id: str):
    """Get status change history for a specific alert.

    Shows the full lifecycle: when it was triggered, acknowledged,
    resolved, etc., with notes and who made each change.

    Args:
        alert_id: Alert UUID (from list_alerts)
    """
    client = _get_client()
    return await asyncio.to_thread(client.alerts.history, alert_id)
