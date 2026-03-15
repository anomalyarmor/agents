"""MCP tool modules.

Importing this package triggers registration of all tools on the
FastMCP instance. Each submodule uses @mcp.tool() to self-register.
"""

from armor_mcp.tools import (  # noqa: F401
    alerts,
    catalog,
    destinations,
    freshness,
    health,
    intelligence,
    quality,
    schema,
)
