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

import armor_mcp.prompts  # noqa: F401
import armor_mcp.resources  # noqa: F401

# Import tools, resources, and prompts to trigger registration.
import armor_mcp.tools  # noqa: F401
from armor_mcp._app import mcp

# ============================================================================
# HTTP Health Check
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Any) -> Any:
    """Health check endpoint for load balancer."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "service": "armor-mcp"})


# ============================================================================
# Agent Discovery Endpoints
# ============================================================================
#
# FastMCP's RemoteAuthProvider publishes oauth-protected-resource metadata at
# /.well-known/oauth-protected-resource/mcp (keyed to the transport path).
# RFC 9728 scanners look at the bare /.well-known/oauth-protected-resource
# first, so we mirror the same content there. The server card is a Model
# Context Protocol discovery document (SEP-1649) so clients pointed at the MCP
# host alone can discover transport, auth, and capabilities.


def _oauth_protected_resource_metadata() -> dict[str, Any]:
    base_url = os.environ.get("MCP_BASE_URL", "https://mcp.anomalyarmor.ai")
    clerk_domain = os.environ.get("CLERK_DOMAIN", "clerk.anomalyarmor.ai")
    return {
        "resource": f"{base_url}/mcp",
        "authorization_servers": [f"https://{clerk_domain}/"],
        "scopes_supported": [],
        "bearer_methods_supported": ["header"],
        "resource_name": "AnomalyArmor MCP Server",
    }


@mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
async def oauth_protected_resource(request: Any) -> Any:
    """RFC 9728 OAuth Protected Resource metadata at the canonical bare path."""
    from starlette.responses import JSONResponse

    return JSONResponse(_oauth_protected_resource_metadata())


@mcp.custom_route("/.well-known/mcp/server-card.json", methods=["GET"])
async def mcp_server_card(request: Any) -> Any:
    """MCP Server Card (SEP-1649) describing this server to AI agents."""
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as pkg_version

    from starlette.responses import JSONResponse

    base_url = os.environ.get("MCP_BASE_URL", "https://mcp.anomalyarmor.ai")
    try:
        server_version = pkg_version("armor-mcp")
    except PackageNotFoundError:
        server_version = "unknown"

    card = {
        "$schema": "https://modelcontextprotocol.io/schemas/server-card/draft-1.json",
        "serverInfo": {
            "name": "AnomalyArmor",
            "title": "AnomalyArmor MCP Server",
            "version": server_version,
            "description": (
                "Data observability tools for AI assistants. Query alerts, monitor "
                "freshness, inspect schema changes, and manage destinations via "
                "natural language."
            ),
            "homepage": "https://www.anomalyarmor.ai",
            "documentation": "https://docs.anomalyarmor.ai/integrations/mcp-server",
            "vendor": {
                "name": "AnomalyArmor",
                "url": "https://www.anomalyarmor.ai",
                "supportEmail": "support@anomalyarmor.ai",
            },
        },
        "transports": [
            {
                "type": "streamable-http",
                "url": f"{base_url}/mcp",
                "preferred": True,
            }
        ],
        "authentication": {
            "type": "oauth2",
            "oauthProtectedResource": f"{base_url}/.well-known/oauth-protected-resource/mcp",
        },
        "capabilities": {
            "tools": {
                "listChanged": True,
                "categories": [
                    "catalog",
                    "destinations",
                    "freshness",
                    "alerts",
                    "health",
                    "recommendations",
                    "intelligence",
                ],
            },
            "resources": {"listChanged": True},
            "prompts": {"listChanged": True},
        },
        "installation": {
            "claudeCode": f"claude mcp add anomalyarmor --transport http {base_url}/mcp",
            "cursor": {
                "mcpServers": {"anomalyarmor": {"url": f"{base_url}/mcp"}},
            },
            "local": {
                "command": "uvx",
                "args": ["armor-mcp"],
                "env": {"ARMOR_API_KEY": "aa_live_your_key_here"},
            },
        },
    }
    return JSONResponse(card)


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
