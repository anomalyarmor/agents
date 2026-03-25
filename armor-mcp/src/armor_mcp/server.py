"""AnomalyArmor MCP Server.

This module provides an MCP server that wraps the AnomalyArmor Python SDK,
exposing data observability tools to AI assistants like Claude Code and Cursor.

Supports two transport modes:
    - stdio (default): API key auth via ARMOR_API_KEY env var
    - HTTP: Clerk OAuth 2.1 via FastMCP's built-in JWTVerifier + RemoteAuthProvider

Usage:
    # Stdio mode (default)
    uvx armor-mcp

    # HTTP mode with Clerk OAuth
    MCP_TRANSPORT=http CLERK_DOMAIN=clerk.example.com uvx armor-mcp
"""

from __future__ import annotations

import os
from typing import Any

from armor_mcp._app import mcp

# Import tools, resources, and prompts to trigger registration.
import armor_mcp.tools  # noqa: F401
import armor_mcp.resources  # noqa: F401
import armor_mcp.prompts  # noqa: F401


# ============================================================================
# HTTP Health Check
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Any) -> Any:
    """Health check endpoint for load balancer."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "service": "armor-mcp"})


# ============================================================================
# Auth Provider (HTTP mode only)
# ============================================================================


def _create_auth_provider() -> Any:
    """Create Clerk OAuth auth provider for HTTP mode."""
    clerk_domain = os.environ.get("CLERK_DOMAIN", "")
    if not clerk_domain:
        return None

    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider

    base_url = os.environ.get("MCP_BASE_URL", "https://mcp.anomalyarmor.ai")

    token_verifier = JWTVerifier(
        jwks_uri=f"https://{clerk_domain}/.well-known/jwks.json",
        issuer=f"https://{clerk_domain}",
        audience=None,
        algorithm="RS256",
    )

    return RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[f"https://{clerk_domain}"],
        base_url=base_url,
        resource_name="AnomalyArmor MCP Server",
    )


# ============================================================================
# Server Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        auth = _create_auth_provider()
        if auth is None:
            raise RuntimeError(
                "CLERK_DOMAIN is required for HTTP mode. "
                "Set CLERK_DOMAIN env var (e.g., clerk.anomalyarmor.ai)."
            )
        mcp.auth = auth
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "3001")),
            stateless_http=True,
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
