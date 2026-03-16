"""Data quality tools: metrics and validity rules."""

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

# -- Metrics -----------------------------------------------------------------


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


# -- Validity Rules ----------------------------------------------------------


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
