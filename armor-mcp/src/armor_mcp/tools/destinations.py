"""Alert destination tools."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from fastmcp.exceptions import ToolError

from armor_mcp._decorators import _attr, sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"destinations", "read"},
)
@sdk_tool
async def list_destinations(
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
    client = _get_client()
    return await asyncio.to_thread(
        client.destinations.list,
        destination_type=destination_type,
        active_only=active_only,
    )


async def _create_slack_destination(client: Any, channel_name: str, name: str | None) -> Any:
    """Handle Slack OAuth discovery, channel lookup, and destination creation.

    Raises:
        ToolError: If no Slack workspace is connected or channel not found.
    """
    # Discover Slack OAuth connection
    try:
        connections = await asyncio.to_thread(client.integrations.list_slack_connections)
    except AttributeError:
        # SDK version doesn't support this method
        connections = []

    if not connections:
        try:
            oauth = await asyncio.to_thread(client.integrations.get_slack_oauth_url)
            oauth_url = _attr(oauth, "url", str(oauth))
        except Exception:
            oauth_url = "Connect Slack via the AnomalyArmor dashboard"
        return {
            "status": "action_required",
            "message": "Connect your Slack workspace first, then retry.",
            "oauth_url": oauth_url,
        }

    connection = connections[0]
    conn_id = _attr(connection, "id")

    # Channel lookup with fuzzy matching
    channels = await asyncio.to_thread(client.integrations.get_slack_channels, conn_id)

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
        raise ToolError(msg)

    channel_id, resolved_name = match
    return await asyncio.to_thread(
        client.integrations.create_slack_destination,
        connection_id=conn_id,
        channel_id=channel_id,
        channel_name=resolved_name,
        name=name or f"Slack #{resolved_name}",
    )


_VALID_DESTINATION_TYPES = ("slack", "webhook", "email")


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False),
    tags={"destinations", "write"},
)
@sdk_tool
async def setup_destination(
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
        return await _create_slack_destination(client, channel_name, name)

    elif destination_type == "webhook":
        return await asyncio.to_thread(
            client.destinations.create,
            destination_type="webhook",
            name=name or "Webhook",
            config={"webhook_url": webhook_url},
        )

    elif destination_type == "email":
        return await asyncio.to_thread(
            client.destinations.create,
            destination_type="email",
            name=name or f"Email: {email}",
            config={"email": email},
        )
    else:
        raise ValueError(
            f"Unhandled type '{destination_type}', "
            f"update dispatch to match _VALID_DESTINATION_TYPES"
        )


_VALID_DEST_ACTIONS = ("get", "update", "delete", "test")


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True),
    tags={"destinations", "read", "write", "delete"},
)
@sdk_tool
async def manage_destination(
    action: str,
    destination_id: str,
    name: str | None = None,
    config: dict | None = None,
    is_active: bool | None = None,
):
    """Manage an existing alert destination: get details, update, delete, or test.

    Use list_destinations to find destination IDs.

    Args:
        action: Operation: "get", "update", "delete", or "test"
        destination_id: Destination UUID (from list_destinations)
        name: New display name (for update)
        config: New config dict (for update, e.g., {"webhook_url": "..."})
        is_active: Enable/disable (for update)
    """
    if action not in _VALID_DEST_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. " f"Must be: {', '.join(_VALID_DEST_ACTIONS)}"
        )

    client = _get_client()

    if action == "get":
        return await asyncio.to_thread(client.alerts.get_destination, destination_id)
    elif action == "update":
        return await asyncio.to_thread(
            client.alerts.update_destination,
            destination_id=destination_id,
            name=name,
            config=config,
            is_active=is_active,
        )
    elif action == "delete":
        return await asyncio.to_thread(client.alerts.delete_destination, destination_id)
    elif action == "test":
        return await asyncio.to_thread(client.alerts.test_destination, destination_id)
    else:
        raise ValueError(
            f"Unhandled action '{action}', update dispatch to match _VALID_DEST_ACTIONS"
        )


_VALID_RULE_DEST_ACTIONS = ("list", "link", "unlink")


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True),
    tags={"destinations", "read", "write", "delete"},
)
@sdk_tool
async def manage_rule_destinations(
    action: str,
    rule_id: str,
    destination_ids: list[str] | None = None,
    destination_id: str | None = None,
):
    """Manage which destinations an alert rule routes to.

    Args:
        action: Operation:
                "list" - list destinations linked to this rule
                "link" - link destinations to the rule (requires destination_ids)
                "unlink" - unlink a destination from the rule (requires destination_id)
        rule_id: Alert rule UUID (from list_alert_rules)
        destination_ids: Destination UUIDs to link (for link action)
        destination_id: Single destination UUID to unlink (for unlink action)
    """
    if action not in _VALID_RULE_DEST_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. "
            f"Must be: {', '.join(_VALID_RULE_DEST_ACTIONS)}"
        )

    client = _get_client()

    if action == "list":
        return await asyncio.to_thread(client.alerts.list_rule_destinations, rule_id)
    elif action == "link":
        if not destination_ids:
            raise ValueError("destination_ids is required for 'link' action")
        return await asyncio.to_thread(
            client.alerts.link_destinations_to_rule,
            rule_id=rule_id,
            destination_ids=destination_ids,
        )
    elif action == "unlink":
        if not destination_id:
            raise ValueError("destination_id is required for 'unlink' action")
        return await asyncio.to_thread(
            client.alerts.unlink_destination_from_rule,
            rule_id=rule_id,
            destination_id=destination_id,
        )
    else:
        raise ValueError(
            f"Unhandled action '{action}', "
            f"update dispatch to match _VALID_RULE_DEST_ACTIONS"
        )
