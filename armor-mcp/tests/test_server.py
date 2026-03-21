"""Tests for server module: tool registration, main(), and validation."""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from armor_mcp._app import mcp


class TestToolRegistration:
    """All 52 consolidated tools must be registered."""

    def test_all_tools_registered(self):
        # Import server to trigger tool registration
        import armor_mcp.server  # noqa: F401

        tool_list = asyncio.run(mcp.list_tools())
        tools = {t.name: t for t in tool_list}

        expected_tools = [
            # Health & Briefings
            "health_summary",
            "get_todays_briefing",
            # Assets
            "list_assets",
            "trigger_asset_discovery",
            "create_asset",
            "manage_asset",
            # Freshness
            "get_freshness_summary",
            "check_freshness",
            "setup_freshness",
            "list_freshness_schedules",
            "manage_freshness_schedule",
            # Schema
            "get_schema_summary",
            "get_schema_monitoring",
            "list_schema_changes",
            "create_schema_baseline",
            "enable_schema_monitoring",
            "disable_schema_monitoring",
            "dry_run_schema",
            # Metrics
            "get_metrics_summary",
            "list_metrics",
            "create_metric",
            "manage_metric",
            # Validity
            "get_validity_summary",
            "list_validity_rules",
            "create_validity_rule",
            "manage_validity_rule",
            # Alerts
            "get_alerts_summary",
            "list_alerts",
            "list_inbox_alerts",
            "update_alert",
            "list_alert_rules",
            "create_alert_rule",
            "manage_alert_rule",
            "get_alert_trends",
            "get_alert_history",
            # Destinations
            "list_destinations",
            "setup_destination",
            "manage_destination",
            "manage_rule_destinations",
            # Intelligence
            "ask_question",
            "generate_intelligence",
            # Lineage & Jobs
            "get_lineage",
            "job_status",
            # Tags
            "create_tag",
            "list_tags",
            "apply_tags",
            # Referential (TECH-935)
            "create_referential_check",
            "manage_referential",
            # Recommendations (TECH-935)
            "recommend",
            # Coverage (TECH-935)
            "get_coverage",
            "manage_coverage",
            # API Keys (TECH-935)
            "get_api_key_info",
        ]

        assert len(expected_tools) == 52

        registered = set(tools.keys())
        missing = set(expected_tools) - registered
        assert not missing, f"Tools not registered: {sorted(missing)}"

        unexpected = registered - set(expected_tools)
        assert not unexpected, f"Unexpected tools registered: {sorted(unexpected)}"


class TestToolValidation:
    """Input validation tests for tools with dispatch logic."""

    def test_update_alert_validates_status(self):
        from armor_mcp.tools.alerts import update_alert

        result = update_alert(alert_id="test-id", status="invalid")
        assert "error" in result
        assert "Invalid status" in result["message"]

    def test_setup_destination_requires_channel_for_slack(self):
        from armor_mcp.tools.destinations import setup_destination

        result = setup_destination(destination_type="slack")
        assert "error" in result
        assert "channel_name" in result["message"]

    def test_setup_destination_requires_url_for_webhook(self):
        from armor_mcp.tools.destinations import setup_destination

        result = setup_destination(destination_type="webhook")
        assert "error" in result
        assert "webhook_url" in result["message"]

    def test_setup_destination_rejects_unknown_type(self):
        from armor_mcp.tools.destinations import setup_destination

        result = setup_destination(destination_type="fax")
        assert "error" in result
        assert "fax" in result["message"]


class TestMain:
    """Tests for server entry point."""

    def test_stdio_mode_is_default(self):
        from armor_mcp.server import main

        with patch.object(mcp, "run") as mock_run:
            with patch.dict(os.environ, {}, clear=False):
                # Remove MCP_TRANSPORT if set
                os.environ.pop("MCP_TRANSPORT", None)
                main()

        mock_run.assert_called_once_with()

    def test_http_mode_requires_clerk_domain(self):
        from armor_mcp.server import main

        with patch.dict(os.environ, {"MCP_TRANSPORT": "http"}, clear=False):
            os.environ.pop("CLERK_DOMAIN", None)
            with pytest.raises(RuntimeError, match="CLERK_DOMAIN is required"):
                main()

    def test_http_mode_configures_auth(self):
        from armor_mcp.server import main

        mock_auth = MagicMock()
        with patch("armor_mcp.server._create_auth_provider", return_value=mock_auth):
            with patch.object(mcp, "run") as mock_run:
                with patch.dict(
                    os.environ,
                    {
                        "MCP_TRANSPORT": "http",
                        "PORT": "8080",
                    },
                ):
                    main()

        assert mcp.auth is mock_auth
        mock_run.assert_called_once_with(
            transport="streamable-http",
            host="0.0.0.0",
            port=8080,
            stateless_http=True,
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
