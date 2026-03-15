"""SDK client factory.

Provides _get_client() which creates or returns an AnomalyArmor SDK client
based on the current transport mode (stdio vs HTTP).
"""

from __future__ import annotations

from typing import Any

# Singleton client instance for stdio mode.
# Thread safety: stdio mode is single-threaded by design (one MCP session
# per process). If FastMCP ever supports concurrent tool calls in stdio
# mode, this will need a threading.Lock.
_client: Any = None


def _get_client() -> Any:
    """Get SDK client for the current request.

    In HTTP mode: creates a per-request client using the Clerk JWT from
    FastMCP's auth context (token passthrough to backend).
    In stdio mode: returns a singleton client using ARMOR_API_KEY from env.

    Returns:
        Initialized AnomalyArmor Client instance.

    Raises:
        RuntimeError: If SDK is not installed or auth is not configured.
    """
    try:
        from anomalyarmor import Client
        from anomalyarmor.exceptions import AuthenticationError
    except ImportError as e:
        raise RuntimeError(
            "anomalyarmor SDK not installed. Run: pip install anomalyarmor"
        ) from e

    # HTTP mode: per-request client with Clerk JWT as Bearer token
    try:
        from fastmcp.server.dependencies import get_access_token

        token = get_access_token()
        if token is not None:
            return Client(api_key=token.token)
    except (ImportError, RuntimeError):
        # ImportError: fastmcp.server.dependencies not available
        # RuntimeError: get_access_token() called outside HTTP request context
        pass

    # Stdio mode: singleton client with API key from env
    global _client
    if _client is None:
        try:
            _client = Client()
        except AuthenticationError as e:
            raise RuntimeError(
                "No API key configured. Set ARMOR_API_KEY env var or create ~/.armor/config.yaml"
            ) from e

    return _client
