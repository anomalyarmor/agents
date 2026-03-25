"""FastMCP application instance.

Separated from server.py to avoid circular imports when tool modules
need to register on the mcp instance.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    "armor-mcp",
    instructions="AnomalyArmor Data Observability Tools",
    mask_error_details=True,
)
