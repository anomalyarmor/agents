"""MCP Apps (ui:// resources) for armor-mcp flagship tools.

Tools in this package attach an HTML ``EmbeddedResource`` content block
to their result, which MCP Apps-capable hosts (Claude Desktop nightly,
Cursor experimental) render inline. Hosts without MCP Apps support
ignore the extra content block and see only the ``TextContent`` JSON
payload that every flagship tool still returns. See TECH-974.
"""

from armor_mcp.apps._plain import to_plain
from armor_mcp.apps.runner import render_app

__all__ = ["render_app", "to_plain"]
