"""MCP prompts for common data observability workflows.

Prompts provide reusable templates that guide LLMs through
multi-step investigation and setup workflows.
"""

from armor_mcp._app import mcp
from fastmcp.prompts import Message


@mcp.prompt(description="Investigate why a data asset is stale")
def investigate_stale(asset_id: str):
    """Investigate why an asset is stale."""
    return [
        Message(
            role="user",
            content=(
                f"Investigate why {asset_id} is stale.\n"
                "1. Check current freshness status with check_freshness\n"
                "2. Get upstream lineage with get_lineage to find dependencies\n"
                "3. Check if upstream assets are also stale\n"
                "4. Review recent alerts with list_alerts for this asset\n"
                "5. Summarize findings and recommend next steps"
            ),
        ),
    ]


@mcp.prompt(description="Triage a fired alert and investigate root cause")
def triage_alert(alert_id: str):
    """Triage a fired alert."""
    return [
        Message(
            role="user",
            content=(
                f"Triage alert {alert_id}.\n"
                "1. Get alert details with get_alert_history\n"
                "2. Identify the affected asset and check its current health\n"
                "3. Check if related assets have similar issues\n"
                "4. Review recent schema changes with list_schema_changes\n"
                "5. Recommend whether to acknowledge, resolve, or escalate"
            ),
        ),
    ]


@mcp.prompt(description="Set up comprehensive monitoring for a data asset")
def setup_monitoring(asset_id: str):
    """Guide through setting up monitoring for an asset."""
    return [
        Message(
            role="user",
            content=(
                f"Set up comprehensive monitoring for asset {asset_id}.\n"
                "1. Check current coverage with get_coverage for this asset\n"
                "2. Set up freshness monitoring with setup_freshness\n"
                "3. Enable schema drift detection with enable_schema_monitoring\n"
                "4. Create key metrics with create_metric for important columns\n"
                "5. Set up alert rules with create_alert_rule for critical events\n"
                "6. Configure a destination with setup_destination if none exist\n"
                "7. Verify final coverage score"
            ),
        ),
    ]


@mcp.prompt(description="Comprehensive data health review across all dimensions")
def data_health_check():
    """Run a comprehensive data health check."""
    return [
        Message(
            role="user",
            content=(
                "Run a comprehensive data health check.\n"
                "1. Get overall health with health_summary\n"
                "2. Review today's briefing with get_todays_briefing\n"
                "3. Check for stale tables with get_freshness_summary\n"
                "4. Review schema drift with get_schema_summary\n"
                "5. Check alert trends with get_alert_trends\n"
                "6. Review coverage gaps with get_coverage\n"
                "7. Summarize findings and prioritize action items"
            ),
        ),
    ]
