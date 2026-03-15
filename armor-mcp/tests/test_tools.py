"""Tests for tool behavior with mocked SDK client.

One representative tool per domain to verify the sdk_tool + _get_client
pipeline works end-to-end without a real SDK connection.
"""

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

_TOOL_MODULES = [
    "armor_mcp.tools.health",
    "armor_mcp.tools.freshness",
    "armor_mcp.tools.schema",
    "armor_mcp.tools.quality",
    "armor_mcp.tools.alerts",
    "armor_mcp.tools.destinations",
    "armor_mcp.tools.intelligence",
    "armor_mcp.tools.catalog",
]


def _mock_client():
    """Create a mock SDK client with all service namespaces."""
    client = MagicMock()
    return client


def _patch_client(mock_client):
    """Context manager to patch _get_client in every tool module.

    Each tool module does `from armor_mcp._client import _get_client`,
    creating a local reference. We must patch each module's local copy.
    """
    stack = ExitStack()
    for mod in _TOOL_MODULES:
        stack.enter_context(patch(f"{mod}._get_client", return_value=mock_client))
    return stack


class TestHealthTools:

    def test_health_summary(self):
        client = _mock_client()
        client.health.summary.return_value = MagicMock(
            model_dump=MagicMock(return_value={"overall_status": "healthy"})
        )

        from armor_mcp.tools.health import health_summary

        with _patch_client(client):
            result = health_summary()

        assert result == {"overall_status": "healthy"}
        client.health.summary.assert_called_once()

    def test_list_assets_with_filter(self):
        client = _mock_client()
        mock_asset = MagicMock()
        mock_asset.model_dump.return_value = {"id": "a1", "source_type": "postgresql"}
        client.assets.list.return_value = [mock_asset]

        from armor_mcp.tools.health import list_assets

        with _patch_client(client):
            result = list_assets(asset_type="postgresql", limit=10)

        assert result == [{"id": "a1", "source_type": "postgresql"}]
        client.assets.list.assert_called_once_with(asset_type="postgresql", limit=10)


class TestFreshnessTools:

    def test_check_freshness(self):
        client = _mock_client()
        client.freshness.check.return_value = MagicMock(
            model_dump=MagicMock(return_value={"tables": []})
        )

        from armor_mcp.tools.freshness import check_freshness

        with _patch_client(client):
            result = check_freshness(asset_id="asset-1")

        assert result == {"tables": []}
        client.freshness.check.assert_called_once_with("asset-1")


class TestSchemaTools:

    def test_get_schema_summary(self):
        client = _mock_client()
        client.schema.summary.return_value = MagicMock(
            model_dump=MagicMock(return_value={"total_changes": 5})
        )

        from armor_mcp.tools.schema import get_schema_summary

        with _patch_client(client):
            result = get_schema_summary()

        assert result == {"total_changes": 5}


class TestQualityTools:

    def test_create_metric(self):
        client = _mock_client()
        client.metrics.create.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "m1", "metric_type": "row_count"})
        )

        from armor_mcp.tools.quality import create_metric

        with _patch_client(client):
            result = create_metric(
                asset_id="a1", table_path="public.orders", metric_type="row_count"
            )

        assert result == {"id": "m1", "metric_type": "row_count"}
        client.metrics.create.assert_called_once_with(
            asset_id="a1",
            table_path="public.orders",
            metric_type="row_count",
            column_name=None,
        )


class TestAlertTools:

    def test_update_alert_acknowledged(self):
        client = _mock_client()
        client.alerts.acknowledge.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "a1", "status": "acknowledged"})
        )

        from armor_mcp.tools.alerts import update_alert

        with _patch_client(client):
            result = update_alert(alert_id="a1", status="acknowledged", notes="on it")

        assert result == {"id": "a1", "status": "acknowledged"}
        client.alerts.acknowledge.assert_called_once_with("a1", notes="on it")

    def test_update_alert_resolved_with_categories(self):
        client = _mock_client()
        client.alerts.resolve.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "a1", "status": "resolved"})
        )

        from armor_mcp.tools.alerts import update_alert

        with _patch_client(client):
            result = update_alert(
                alert_id="a1",
                status="resolved",
                notes="fixed",
                action_category="reran_job",
                root_cause_category="pipeline_failure",
            )

        assert result["status"] == "resolved"
        client.alerts.resolve.assert_called_once_with(
            "a1",
            notes="fixed",
            action_category="reran_job",
            root_cause_category="pipeline_failure",
        )

    def test_update_alert_snoozed(self):
        client = _mock_client()
        client.alerts.snooze.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "a1", "status": "snoozed"})
        )

        from armor_mcp.tools.alerts import update_alert

        with _patch_client(client):
            result = update_alert(alert_id="a1", status="snoozed", duration_hours=48)

        assert result["status"] == "snoozed"
        client.alerts.snooze.assert_called_once_with("a1", duration_hours=48, notes=None)


class TestDestinationTools:

    def test_setup_webhook_destination(self):
        client = _mock_client()
        client.destinations.create.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "d1", "type": "webhook"})
        )

        from armor_mcp.tools.destinations import setup_destination

        with _patch_client(client):
            result = setup_destination(
                destination_type="webhook",
                webhook_url="https://example.com/hook",
            )

        assert result == {"id": "d1", "type": "webhook"}
        client.destinations.create.assert_called_once_with(
            destination_type="webhook",
            name="Webhook",
            config={"webhook_url": "https://example.com/hook"},
        )

    def test_setup_email_destination(self):
        client = _mock_client()
        client.destinations.create.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "d2", "type": "email"})
        )

        from armor_mcp.tools.destinations import setup_destination

        with _patch_client(client):
            result = setup_destination(
                destination_type="email",
                email="ops@example.com",
                name="Ops Team",
            )

        assert result == {"id": "d2", "type": "email"}
        client.destinations.create.assert_called_once_with(
            destination_type="email",
            name="Ops Team",
            config={"email": "ops@example.com"},
        )

    def test_setup_slack_no_workspace(self):
        """Slack destination returns ToolError with oauth_url when no workspace connected."""
        client = _mock_client()
        client.integrations.list_slack_connections.return_value = []
        client.integrations.get_slack_oauth_url.side_effect = AttributeError

        from armor_mcp.tools.destinations import setup_destination

        with _patch_client(client):
            result = setup_destination(
                destination_type="slack",
                channel_name="alerts",
            )

        assert result["error"] == "NoSlackConnection"
        assert "oauth_url" in result

    def test_setup_slack_channel_not_found(self):
        """Slack destination returns ToolError with suggestions when channel not found."""
        client = _mock_client()

        mock_conn = MagicMock()
        mock_conn.id = "conn-1"
        client.integrations.list_slack_connections.return_value = [mock_conn]

        # "alerts" is a substring of "alerts-prod", so fuzzy match triggers
        mock_ch = MagicMock()
        mock_ch.name = "alerts-prod"
        mock_ch.id = "C123"
        client.integrations.get_slack_channels.return_value = [mock_ch]

        from armor_mcp.tools.destinations import setup_destination

        with _patch_client(client):
            result = setup_destination(
                destination_type="slack",
                channel_name="alerts",
            )

        assert result["error"] == "NotFoundError"
        assert "alerts" in result["message"]
        assert "alerts-prod" in result["message"]  # fuzzy match suggestion

    def test_setup_slack_success(self):
        """Slack destination auto-discovers connection and finds channel."""
        client = _mock_client()

        mock_conn = MagicMock()
        mock_conn.id = "conn-1"
        client.integrations.list_slack_connections.return_value = [mock_conn]

        mock_ch = MagicMock()
        mock_ch.name = "alerts"
        mock_ch.id = "C123"
        client.integrations.get_slack_channels.return_value = [mock_ch]

        client.integrations.create_slack_destination.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "d3", "type": "slack"})
        )

        from armor_mcp.tools.destinations import setup_destination

        with _patch_client(client):
            result = setup_destination(
                destination_type="slack",
                channel_name="alerts",
            )

        assert result == {"id": "d3", "type": "slack"}
        client.integrations.create_slack_destination.assert_called_once_with(
            connection_id="conn-1",
            channel_id="C123",
            channel_name="alerts",
            name="Slack #alerts",
        )


class TestIntelligenceTools:

    def test_ask_question(self):
        client = _mock_client()
        client.intelligence.ask.return_value = MagicMock(
            model_dump=MagicMock(return_value={"answer": "42"})
        )

        from armor_mcp.tools.intelligence import ask_question

        with _patch_client(client):
            result = ask_question(question="What is the meaning?")

        assert result == {"answer": "42"}


class TestCatalogTools:

    def test_get_lineage(self):
        client = _mock_client()
        client.lineage.get.return_value = MagicMock(
            model_dump=MagicMock(return_value={"nodes": [], "edges": []})
        )

        from armor_mcp.tools.catalog import get_lineage

        with _patch_client(client):
            result = get_lineage(asset_id="a1", depth=3, direction="upstream")

        assert result == {"nodes": [], "edges": []}
        client.lineage.get.assert_called_once_with(
            asset_id="a1", depth=3, direction="upstream",
        )

    def test_apply_tags(self):
        client = _mock_client()
        client.tags.apply.return_value = MagicMock(
            model_dump=MagicMock(return_value={"applied": ["pii", "sensitive"]})
        )

        from armor_mcp.tools.catalog import apply_tags

        with _patch_client(client):
            result = apply_tags(
                asset_id="a1",
                object_path="public.users.email",
                tags=["pii", "sensitive"],
                object_type="column",
            )

        assert result == {"applied": ["pii", "sensitive"]}
