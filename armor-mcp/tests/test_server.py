"""Tests for server module: tool registration, main(), and validation."""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from armor_mcp._app import mcp
from fastmcp.exceptions import ToolError


class TestToolRegistration:
    """All 53 consolidated tools must be registered."""

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
            "cancel_job",
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

        assert len(expected_tools) == 53

        registered = set(tools.keys())
        missing = set(expected_tools) - registered
        assert not missing, f"Tools not registered: {sorted(missing)}"

        unexpected = registered - set(expected_tools)
        assert not unexpected, f"Unexpected tools registered: {sorted(unexpected)}"


class TestToolValidation:
    """Input validation tests for tools with dispatch logic."""

    def test_update_alert_validates_status(self):
        from armor_mcp.tools.alerts import update_alert

        with pytest.raises(ToolError, match="Invalid status"):
            asyncio.run(update_alert(alert_id="test-id", status="invalid"))

    def test_setup_destination_requires_channel_for_slack(self):
        from armor_mcp.tools.destinations import setup_destination

        with pytest.raises(ToolError, match="channel_name"):
            asyncio.run(setup_destination(destination_type="slack"))

    def test_setup_destination_requires_url_for_webhook(self):
        from armor_mcp.tools.destinations import setup_destination

        with pytest.raises(ToolError, match="webhook_url"):
            asyncio.run(setup_destination(destination_type="webhook"))

    def test_setup_destination_rejects_unknown_type(self):
        from armor_mcp.tools.destinations import setup_destination

        with pytest.raises(ToolError, match="fax"):
            asyncio.run(setup_destination(destination_type="fax"))


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


class TestAgentDiscoveryEndpoints:
    """Well-known endpoints that advertise the MCP server to AI agents."""

    def test_oauth_protected_resource_matches_fastmcp_variant(self):
        import json

        from armor_mcp.server import oauth_protected_resource

        env = {
            "MCP_BASE_URL": "https://mcp.anomalyarmor.ai",
            "CLERK_DOMAIN": "clerk.anomalyarmor.ai",
        }
        with patch.dict(os.environ, env, clear=False):
            response = asyncio.run(oauth_protected_resource(request=MagicMock()))

        body = json.loads(response.body)
        assert body == {
            "resource": "https://mcp.anomalyarmor.ai/mcp",
            "authorization_servers": ["https://clerk.anomalyarmor.ai/"],
            "scopes_supported": [],
            "bearer_methods_supported": ["header"],
            "resource_name": "AnomalyArmor MCP Server",
        }

    def test_mcp_server_card_core_fields(self):
        import json

        from armor_mcp.server import mcp_server_card

        with patch.dict(
            os.environ, {"MCP_BASE_URL": "https://mcp.anomalyarmor.ai"}, clear=False
        ):
            response = asyncio.run(mcp_server_card(request=MagicMock()))

        card = json.loads(response.body)
        assert card["serverInfo"]["name"] == "AnomalyArmor"
        assert card["transports"][0]["url"] == "https://mcp.anomalyarmor.ai/mcp"
        assert card["transports"][0]["type"] == "streamable-http"
        assert card["authentication"]["type"] == "oauth2"
        assert (
            card["authentication"]["oauthProtectedResource"]
            == "https://mcp.anomalyarmor.ai/.well-known/oauth-protected-resource/mcp"
        )

    def test_mcp_server_card_top_level_identity(self):
        """RFC / scanner clients look for name/description/version at the root."""
        import json

        from armor_mcp.server import mcp_server_card

        with patch.dict(
            os.environ, {"MCP_BASE_URL": "https://mcp.anomalyarmor.ai"}, clear=False
        ):
            response = asyncio.run(mcp_server_card(request=MagicMock()))

        card = json.loads(response.body)
        assert card["name"] == "AnomalyArmor"
        assert "Data observability" in card["description"]
        assert isinstance(card["version"], str)
        assert card["version"] == card["serverInfo"]["version"]
        assert card["serverUrl"] == "https://mcp.anomalyarmor.ai/mcp"

    def test_oauth_authorization_server_metadata(self):
        """RFC 8414 metadata must advertise PKCE S256 and point at the Clerk issuer."""
        import json

        from armor_mcp.server import oauth_authorization_server

        with patch.dict(
            os.environ, {"CLERK_DOMAIN": "clerk.anomalyarmor.ai"}, clear=False
        ):
            response = asyncio.run(oauth_authorization_server(request=MagicMock()))

        metadata = json.loads(response.body)
        assert metadata["issuer"] == "https://clerk.anomalyarmor.ai"
        assert (
            metadata["authorization_endpoint"]
            == "https://clerk.anomalyarmor.ai/oauth/authorize"
        )
        assert metadata["token_endpoint"] == "https://clerk.anomalyarmor.ai/oauth/token"
        assert metadata["code_challenge_methods_supported"] == ["S256"]
        assert "authorization_code" in metadata["grant_types_supported"]
        assert "refresh_token" in metadata["grant_types_supported"]

    def test_openid_configuration_matches_authorization_server(self):
        """The OIDC alias returns the same payload as oauth-authorization-server."""
        import json

        from armor_mcp.server import oauth_authorization_server, openid_configuration

        with patch.dict(
            os.environ, {"CLERK_DOMAIN": "clerk.anomalyarmor.ai"}, clear=False
        ):
            auth_resp = asyncio.run(oauth_authorization_server(request=MagicMock()))
            oidc_resp = asyncio.run(openid_configuration(request=MagicMock()))

        assert json.loads(auth_resp.body) == json.loads(oidc_resp.body)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
