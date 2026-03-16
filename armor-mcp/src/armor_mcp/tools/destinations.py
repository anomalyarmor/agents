"""Alert destination tools."""

from __future__ import annotations

from typing import Any

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import ToolError, _attr, sdk_tool


@mcp.tool()
@sdk_tool
def list_destinations(
    destination_type: str | None = None,
    active_only: bool = True,
):
    """List configured alert destinations (Slack, email, webhook).

    Returns destination IDs needed for create_alert_rule. Use setup_destination
    to create new destinations.

    Args:
        destination_type: Filter by type: "slack", "webhook", "email"
        active_only: Only return active destinations (default True)
    """
    return _get_client().destinations.list(
        destination_type=destination_type,
        active_only=active_only,
    )


def _create_slack_destination(client: Any, channel_name: str, name: str | None) -> Any:
    """Handle Slack OAuth discovery, channel lookup, and destination creation.

    Raises:
        ToolError: If no Slack workspace is connected or channel not found.
    """
    # Discover Slack OAuth connection
    try:
        connections = client.integrations.list_slack_connections()
    except AttributeError:
        # SDK version doesn't support this method
        connections = []

    if not connections:
        try:
            oauth = client.integrations.get_slack_oauth_url()
            oauth_url = _attr(oauth, "url", str(oauth))
        except Exception:
            oauth_url = "Connect Slack via the AnomalyArmor dashboard"
        raise ToolError(
            "Connect your Slack workspace first, then retry.",
            error_type="NoSlackConnection",
            oauth_url=oauth_url,
        )

    connection = connections[0]
    conn_id = _attr(connection, "id")

    # Channel lookup with fuzzy matching
    channels = client.integrations.get_slack_channels(conn_id)

    match = None
    close_matches = []
    for ch in channels:
        ch_name = _attr(ch, "name", "")
        ch_id = _attr(ch, "id", "")
        if ch_name == channel_name:
            match = (ch_id, ch_name)
            break
        if channel_name in ch_name:
            close_matches.append(ch_name)

    if not match:
        msg = f"Channel '#{channel_name}' not found."
        if close_matches:
            msg += f" Similar: {', '.join(close_matches[:5])}"
        raise ToolError(msg, error_type="NotFoundError")

    channel_id, resolved_name = match
    return client.integrations.create_slack_destination(
        connection_id=conn_id,
        channel_id=channel_id,
        channel_name=resolved_name,
        name=name or f"Slack #{resolved_name}",
    )


_VALID_DESTINATION_TYPES = ("slack", "webhook", "email")


@mcp.tool()
@sdk_tool
def setup_destination(
    destination_type: str,
    name: str | None = None,
    channel_name: str | None = None,
    webhook_url: str | None = None,
    email: str | None = None,
):
    """Create an alert destination with auto-discovery.

    For Slack: provide channel_name (auto-discovers OAuth connection).
    For webhook: provide webhook_url.
    For email: provide email address.
    After creating, use create_alert_rule to route alerts to the destination.

    Args:
        destination_type: Type of destination: "slack", "webhook", or "email"
        name: Display name for the destination (auto-generated if omitted)
        channel_name: Slack channel name without # (required for Slack)
        webhook_url: Full webhook URL (required for webhook)
        email: Email address (required for email)
    """
    if destination_type not in _VALID_DESTINATION_TYPES:
        raise ValueError(
            f"Unknown type '{destination_type}'. "
            f"Use {', '.join(_VALID_DESTINATION_TYPES)}."
        )

    if destination_type == "slack" and not channel_name:
        raise ValueError("channel_name is required for Slack destinations")
    if destination_type == "webhook" and not webhook_url:
        raise ValueError("webhook_url is required for webhook destinations")
    if destination_type == "email" and not email:
        raise ValueError("email is required for email destinations")

    client = _get_client()

    if destination_type == "slack":
        return _create_slack_destination(client, channel_name, name)

    elif destination_type == "webhook":
        return client.destinations.create(
            destination_type="webhook",
            name=name or "Webhook",
            config={"webhook_url": webhook_url},
        )

    elif destination_type == "email":
        return client.destinations.create(
            destination_type="email",
            name=name or f"Email: {email}",
            config={"email": email},
        )
    else:
        raise ValueError(
            f"Unhandled type '{destination_type}', "
            f"update dispatch to match _VALID_DESTINATION_TYPES"
        )
