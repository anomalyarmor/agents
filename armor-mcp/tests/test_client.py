"""Tests for _client module: _get_client factory."""

from unittest.mock import MagicMock, patch

import pytest

import armor_mcp._client as client_mod


class TestGetClient:
    """Tests for _get_client factory."""

    def setup_method(self):
        # Reset singleton between tests
        client_mod._client = None

    def test_raises_when_sdk_not_installed(self):
        with patch.dict("sys.modules", {"anomalyarmor": None}):
            with pytest.raises(RuntimeError, match="SDK not installed"):
                client_mod._get_client()

    def test_stdio_mode_creates_singleton(self):
        mock_client = MagicMock()
        mock_client_class = MagicMock(return_value=mock_client)

        with patch.dict("sys.modules", {
            "anomalyarmor": MagicMock(Client=mock_client_class),
            "anomalyarmor.exceptions": MagicMock(AuthenticationError=Exception),
        }):
            # Patch get_access_token to simulate stdio mode (no HTTP context)
            with patch.dict("sys.modules", {
                "fastmcp.server.dependencies": None,
            }):
                result1 = client_mod._get_client()
                result2 = client_mod._get_client()

        assert result1 is mock_client
        assert result2 is mock_client
        mock_client_class.assert_called_once()  # singleton, only one instantiation

    def test_stdio_mode_raises_on_auth_error(self):
        auth_error = type("AuthenticationError", (Exception,), {})

        mock_module = MagicMock()
        mock_module.Client.side_effect = auth_error("no key")

        mock_exc_module = MagicMock()
        mock_exc_module.AuthenticationError = auth_error

        with patch.dict("sys.modules", {
            "anomalyarmor": mock_module,
            "anomalyarmor.exceptions": mock_exc_module,
            "fastmcp.server.dependencies": None,
        }):
            with pytest.raises(RuntimeError, match="No API key configured"):
                client_mod._get_client()

    def test_http_mode_creates_per_request_client(self):
        mock_client = MagicMock()
        mock_client_class = MagicMock(return_value=mock_client)

        mock_token = MagicMock()
        mock_token.token = "clerk_jwt_token"

        mock_deps = MagicMock()
        mock_deps.get_access_token = MagicMock(return_value=mock_token)

        with patch.dict("sys.modules", {
            "anomalyarmor": MagicMock(Client=mock_client_class),
            "anomalyarmor.exceptions": MagicMock(AuthenticationError=Exception),
            "fastmcp.server.dependencies": mock_deps,
        }):
            result = client_mod._get_client()

        assert result is mock_client
        mock_client_class.assert_called_once_with(api_key="clerk_jwt_token")
