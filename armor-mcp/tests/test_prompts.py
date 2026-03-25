"""Tests for MCP prompts."""

import asyncio

from armor_mcp._app import mcp


def _get_text(message):
    """Extract text from a Message, handling both str and TextContent."""
    content = message.content
    if hasattr(content, "text"):
        return content.text
    return str(content)


class TestPrompts:
    """All prompts must be registered and return Message lists."""

    def test_prompts_registered(self):
        import armor_mcp.server  # noqa: F401

        prompts = asyncio.run(mcp.list_prompts())
        names = {p.name for p in prompts}
        assert "investigate_stale" in names
        assert "triage_alert" in names
        assert "setup_monitoring" in names
        assert "data_health_check" in names

    def test_investigate_stale_returns_messages(self):
        from armor_mcp.prompts import investigate_stale

        result = investigate_stale(asset_id="test-asset-123")
        assert len(result) == 1
        assert result[0].role == "user"
        text = _get_text(result[0])
        assert "test-asset-123" in text
        assert "check_freshness" in text
        assert "get_lineage" in text

    def test_triage_alert_returns_messages(self):
        from armor_mcp.prompts import triage_alert

        result = triage_alert(alert_id="alert-456")
        assert len(result) == 1
        text = _get_text(result[0])
        assert "alert-456" in text
        assert "get_alert_history" in text

    def test_setup_monitoring_returns_messages(self):
        from armor_mcp.prompts import setup_monitoring

        result = setup_monitoring(asset_id="asset-789")
        assert len(result) == 1
        text = _get_text(result[0])
        assert "asset-789" in text
        assert "setup_freshness" in text
        assert "enable_schema_monitoring" in text

    def test_data_health_check_returns_messages(self):
        from armor_mcp.prompts import data_health_check

        result = data_health_check()
        assert len(result) == 1
        text = _get_text(result[0])
        assert "health_summary" in text
        assert "get_freshness_summary" in text
