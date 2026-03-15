"""Alert management tools."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


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


_VALID_ALERT_STATUSES = ("acknowledged", "resolved", "dismissed", "snoozed")


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
    if status not in _VALID_ALERT_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Must be: {', '.join(_VALID_ALERT_STATUSES)}"
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
    else:
        raise ValueError(f"Unhandled status '{status}', update dispatch to match _VALID_ALERT_STATUSES")


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
