"""Tests for MCP server tools (TECH-904: consolidated from 74 to 29)."""

import asyncio
from unittest.mock import Mock

import pytest

from armor_mcp.server import sdk_tool


class TestSdkTool:
    """Tests for the sdk_tool decorator."""

    def test_sdk_tool_handles_model_dump(self):
        mock_model = Mock()
        mock_model.model_dump.return_value = {"key": "value"}

        @sdk_tool
        def test_func():
            return mock_model

        result = test_func()
        assert result == {"key": "value"}
        mock_model.model_dump.assert_called_once()

    def test_sdk_tool_handles_list_of_models(self):
        mock_model1 = Mock()
        mock_model1.model_dump.return_value = {"id": 1}
        mock_model2 = Mock()
        mock_model2.model_dump.return_value = {"id": 2}

        @sdk_tool
        def test_func():
            return [mock_model1, mock_model2]

        result = test_func()
        assert result == [{"id": 1}, {"id": 2}]

    def test_sdk_tool_handles_dict(self):
        @sdk_tool
        def test_func():
            return {"already": "dict"}

        result = test_func()
        assert result == {"already": "dict"}

    def test_sdk_tool_handles_exceptions(self):
        @sdk_tool
        def test_func():
            raise ValueError("test error")

        result = test_func()
        assert result["error"] == "ValueError"
        assert "test error" in result["message"]


class TestToolRegistration:
    """Tests for tool registration (TECH-904)."""

    def test_all_tools_registered(self):
        """All consolidated tools are registered with FastMCP."""
        from armor_mcp.server import mcp

        tool_list = asyncio.run(mcp.list_tools())
        tools = {t.name: t for t in tool_list}

        expected_tools = [
            # Health & Discovery
            "health_summary",
            "list_assets",
            "trigger_asset_discovery",
            # Freshness
            "get_freshness_summary",
            "check_freshness",
            "setup_freshness",
            "list_freshness_schedules",
            # Schema
            "get_schema_summary",
            "list_schema_changes",
            "create_schema_baseline",
            "enable_schema_monitoring",
            "disable_schema_monitoring",
            "dry_run_schema",
            # Metrics
            "list_metrics",
            "create_metric",
            # Validity
            "list_validity_rules",
            "create_validity_rule",
            # Alerts
            "list_alerts",
            "update_alert",
            "list_alert_rules",
            "create_alert_rule",
            # Destinations
            "list_destinations",
            "setup_destination",
            # Intelligence
            "ask_question",
            "generate_intelligence",
            # Lineage & Jobs
            "get_lineage",
            "job_status",
            # Tags
            "list_tags",
            "apply_tags",
        ]

        assert len(expected_tools) == 29

        registered = set(tools.keys())
        missing = set(expected_tools) - registered
        assert not missing, f"Tools not registered: {sorted(missing)}"

        unexpected = registered - set(expected_tools)
        assert not unexpected, f"Unexpected tools registered: {sorted(unexpected)}"

    def test_update_alert_validates_status(self):
        """update_alert rejects invalid status values."""
        from armor_mcp.server import update_alert

        # The sdk_tool wrapper catches exceptions and returns error dict
        result = update_alert(alert_id="test-id", status="invalid")
        assert "error" in result
        assert "Invalid status" in result["message"]

    def test_setup_destination_requires_channel_for_slack(self):
        """setup_destination requires channel_name for Slack."""
        from armor_mcp.server import setup_destination

        result = setup_destination(destination_type="slack")
        assert "error" in result
        assert "channel_name" in result["message"]

    def test_setup_destination_requires_url_for_webhook(self):
        """setup_destination requires webhook_url for webhook."""
        from armor_mcp.server import setup_destination

        result = setup_destination(destination_type="webhook")
        assert "error" in result
        assert "webhook_url" in result["message"]

    def test_setup_destination_rejects_unknown_type(self):
        """setup_destination rejects unknown destination types."""
        from armor_mcp.server import setup_destination

        result = setup_destination(destination_type="fax")
        assert "error" in result
        assert "fax" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
