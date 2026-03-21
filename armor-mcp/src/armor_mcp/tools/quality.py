"""Data quality tools: metrics and validity rules."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

# -- Metrics -----------------------------------------------------------------


@mcp.tool()
@sdk_tool
def get_metrics_summary(asset_id: str):
    """Get metrics monitoring summary for an asset.

    Shows total metrics, active count, anomaly count, and per-type breakdown.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().metrics.summary(asset_id)


@mcp.tool()
@sdk_tool
def list_metrics(asset_id: str, limit: int = 25):
    """List data quality metrics configured for an asset.

    Shows metric type, table, column, and active status.
    Use create_metric to add new metrics.

    Args:
        asset_id: Asset UUID (from list_assets)
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
    """Create a data quality metric for a table.

    Use explore to find table paths and column names.

    Args:
        asset_id: Asset UUID (from list_assets)
        table_path: Full table path (e.g., "public.orders")
        metric_type: Type of metric: "row_count", "null_rate", "unique_rate",
                     "min", "max", "mean", "stddev"
        column_name: Column to monitor (required for column-level metrics like
                     null_rate, mean, etc.)
    """
    return _get_client().metrics.create(
        asset_id=asset_id,
        table_path=table_path,
        metric_type=metric_type,
        column_name=column_name,
    )


_VALID_METRIC_ACTIONS = ("get", "update", "delete", "capture", "snapshots")


@mcp.tool()
@sdk_tool
def manage_metric(
    action: str,
    asset_id: str,
    metric_id: str,
    is_active: bool | None = None,
    capture_interval: str | None = None,
    sensitivity: float | None = None,
    limit: int = 100,
):
    """Manage an existing metric: get details, update, delete, trigger capture, or view snapshots.

    Use list_metrics to find metric IDs.

    Args:
        action: Operation:
                "get" - get metric details and current value
                "update" - update metric settings
                "delete" - delete the metric
                "capture" - trigger an immediate metric capture
                "snapshots" - view historical metric values
        asset_id: Asset UUID (from list_assets)
        metric_id: Metric UUID (from list_metrics)
        is_active: Enable/disable metric (for update)
        capture_interval: New capture interval (for update)
        sensitivity: Anomaly detection sensitivity 0.0-1.0 (for update)
        limit: Max snapshots to return (for snapshots action, default 100)
    """
    if action not in _VALID_METRIC_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_METRIC_ACTIONS)}"
        )

    client = _get_client()

    if action == "get":
        return client.metrics.get(asset_id, metric_id)
    elif action == "update":
        return client.metrics.update(
            asset_id=asset_id,
            metric_id=metric_id,
            is_active=is_active,
            capture_interval=capture_interval,
            sensitivity=sensitivity,
        )
    elif action == "delete":
        return client.metrics.delete(asset_id, metric_id)
    elif action == "capture":
        return client.metrics.capture(asset_id, metric_id)
    elif action == "snapshots":
        return client.metrics.snapshots(asset_id, metric_id, limit=limit)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_METRIC_ACTIONS"
        )


# -- Validity Rules ----------------------------------------------------------


@mcp.tool()
@sdk_tool
def get_validity_summary(asset_id: str):
    """Get validity rules summary for an asset.

    Shows total rules, active count, failing count, and per-type breakdown.

    Args:
        asset_id: Asset UUID (from list_assets)
    """
    return _get_client().validity.summary(asset_id)


@mcp.tool()
@sdk_tool
def list_validity_rules(asset_id: str, limit: int = 25):
    """List data validity rules configured for an asset.

    Shows rule type, table, column, and active status.
    Use create_validity_rule to add new rules.

    Args:
        asset_id: Asset UUID (from list_assets)
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
    """Create a data validity rule for a specific column.

    Checks column values against defined constraints. Use explore to find
    table and column names.

    Args:
        asset_id: Asset UUID (from list_assets)
        table_path: Full table path (e.g., "public.users")
        column_name: Column to validate
        rule_type: Type of check: "regex_match", "allowed_values", "range_bounds",
                   "format", "length_bounds"
        rule_config: Config for the rule type. Examples:
                     {"pattern": "^[A-Z]"} for regex_match,
                     {"values": ["a","b"]} for allowed_values,
                     {"min": 0, "max": 100} for range_bounds
        name: Human-readable rule name (auto-generated if omitted)
        severity: Alert severity when rule fails: "error" (default), "warning", "critical"
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


_VALID_VALIDITY_ACTIONS = ("get", "update", "delete", "check", "results")


@mcp.tool()
@sdk_tool
def manage_validity_rule(
    action: str,
    asset_id: str,
    rule_id: str,
    name: str | None = None,
    rule_config: dict | None = None,
    severity: str | None = None,
    is_active: bool | None = None,
    limit: int = 25,
):
    """Manage an existing validity rule: get details, update, delete, check, or view results.

    Use list_validity_rules to find rule IDs.

    Args:
        action: Operation:
                "get" - get rule details
                "update" - update rule settings
                "delete" - delete the rule
                "check" - run the validity check now
                "results" - view recent check results
        asset_id: Asset UUID (from list_assets)
        rule_id: Validity rule UUID (from list_validity_rules)
        name: New name (for update)
        rule_config: New rule config (for update)
        severity: New severity (for update)
        is_active: Enable/disable (for update)
        limit: Max results to return (for results action, default 25)
    """
    if action not in _VALID_VALIDITY_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_VALIDITY_ACTIONS)}"
        )

    client = _get_client()

    if action == "get":
        return client.validity.get(asset_id, rule_id)
    elif action == "update":
        return client.validity.update(
            asset_id=asset_id,
            rule_id=rule_id,
            name=name,
            rule_config=rule_config,
            severity=severity,
            is_active=is_active,
        )
    elif action == "delete":
        return client.validity.delete(asset_id, rule_id)
    elif action == "check":
        return client.validity.check(asset_id=asset_id, rule_id=rule_id)
    elif action == "results":
        return client.validity.results(asset_id, rule_id, limit=limit)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_VALIDITY_ACTIONS"
        )
