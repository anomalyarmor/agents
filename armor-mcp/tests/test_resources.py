"""Tests for MCP resources."""

import asyncio
import json
from unittest.mock import MagicMock, patch

from armor_mcp._app import mcp


def _mock_client():
    return MagicMock()


def _patch_client(client):
    return patch("armor_mcp.resources._get_client", return_value=client)


class TestResources:
    """All resources must be registered and return JSON strings."""

    def test_resources_registered(self):
        import armor_mcp.server  # noqa: F401

        resources = asyncio.run(mcp.list_resources())
        uris = {str(r.uri) for r in resources}
        assert "armor://health" in uris
        assert "armor://assets" in uris
        assert "armor://alerts/summary" in uris
        assert "armor://freshness/summary" in uris

    def test_resource_templates_registered(self):
        import armor_mcp.server  # noqa: F401

        templates = asyncio.run(mcp.list_resource_templates())
        uris = {str(t.uri_template) for t in templates}
        assert "armor://assets/{asset_id}/schema" in uris

    def test_health_resource_returns_json(self):
        client = _mock_client()
        client.health.summary.return_value = MagicMock(
            model_dump=MagicMock(return_value={"overall_status": "healthy"})
        )

        from armor_mcp.resources import health_resource

        with _patch_client(client):
            result = asyncio.run(health_resource())

        parsed = json.loads(result)
        assert parsed == {"overall_status": "healthy"}

    def test_assets_resource_returns_json(self):
        mock_asset = MagicMock()
        mock_asset.model_dump.return_value = {"id": "a1", "name": "prod-db"}
        client = _mock_client()
        client.assets.list.return_value = [mock_asset]

        from armor_mcp.resources import assets_resource

        with _patch_client(client):
            result = asyncio.run(assets_resource())

        parsed = json.loads(result)
        assert parsed == [{"id": "a1", "name": "prod-db"}]

    def test_alerts_summary_resource_returns_json(self):
        client = _mock_client()
        client.alerts.summary.return_value = MagicMock(
            model_dump=MagicMock(return_value={"total": 5, "critical": 1})
        )

        from armor_mcp.resources import alerts_summary_resource

        with _patch_client(client):
            result = asyncio.run(alerts_summary_resource())

        parsed = json.loads(result)
        assert parsed == {"total": 5, "critical": 1}
