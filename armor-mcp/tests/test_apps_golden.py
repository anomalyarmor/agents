"""Golden test: flagship tools' JSON content must match pre-change output.

TECH-974 switched the 4 flagship tools from returning a plain dict/list
(which FastMCP auto-wrapped into a single ``TextContent``) to returning
a two-element content-block list: a ``TextContent(text=json.dumps(...))``
plus an ``EmbeddedResource`` for MCP Apps-capable hosts.

Hosts that don't render ``EmbeddedResource`` should see *byte-identical*
JSON to what they saw before. This test asserts that by:

1. Calling the wired tool's inner coroutine with a stub client.
2. Extracting the ``TextContent.text`` (the JSON blob).
3. Comparing it to ``json.dumps(payload, default=str)`` — which is what
   the pre-change FastMCP wrapping would have produced after
   ``_serialize`` ran.

The 49 untouched tools are implicitly covered by the existing
``tests/test_decorators.py`` / ``tests/test_tools.py`` which exercise
``_serialize`` — this file just pins the 4 we changed.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from armor_mcp.tools.catalog import get_lineage
from armor_mcp.tools.freshness import check_freshness, get_freshness_summary
from armor_mcp.tools.health import health_summary
from armor_mcp.tools.schema import list_schema_changes
from mcp.types import EmbeddedResource, TextContent


class _StubClient:
    """In-memory stand-in for ``anomalyarmor.Client``.

    Each attribute chain (``client.freshness.summary``,
    ``client.schema.changes``, etc.) resolves to a no-arg callable that
    returns the canned payload registered for that path.
    """

    def __init__(self, responses: dict[str, Any]) -> None:
        self._responses = responses

    def __getattr__(self, name: str) -> "_StubNamespace":
        return _StubNamespace(name, self._responses)


class _StubNamespace:
    def __init__(self, prefix: str, responses: dict[str, Any]) -> None:
        self._prefix = prefix
        self._responses = responses

    def __getattr__(self, name: str) -> Any:
        key = f"{self._prefix}.{name}"
        value = self._responses.get(key)

        def _call(*_args: Any, **_kwargs: Any) -> Any:
            return value

        return _call


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _split(result: list) -> tuple[str, EmbeddedResource]:
    """Assert ``result`` is the [TextContent, EmbeddedResource] pair and
    return the JSON text + resource for inspection."""
    assert isinstance(result, list)
    assert len(result) == 2
    text_block, resource_block = result
    assert isinstance(text_block, TextContent)
    assert isinstance(resource_block, EmbeddedResource)
    return text_block.text, resource_block


@pytest.fixture
def patched_client(monkeypatch: pytest.MonkeyPatch):
    """Patch ``_get_client`` in all four touched tool modules.

    Returns a function that takes canned responses and installs the stub.
    """

    def _install(responses: dict[str, Any]) -> None:
        stub = _StubClient(responses)
        for module in (
            "armor_mcp.tools.freshness",
            "armor_mcp.tools.schema",
            "armor_mcp.tools.health",
            "armor_mcp.tools.catalog",
        ):
            monkeypatch.setattr(f"{module}._get_client", lambda stub=stub: stub)

    return _install


def test_get_freshness_summary_json_matches_pretech974_serialization(
    patched_client: Any,
) -> None:
    payload = {
        "total_assets": 14,
        "fresh_count": 10,
        "stale_count": 3,
        "unknown_count": 1,
        "disabled_count": 0,
        "freshness_rate": 71.4,
    }
    patched_client({"freshness.summary": payload})
    result = _run(get_freshness_summary())
    text, _ = _split(result)
    assert text == json.dumps(payload, default=str)


def test_check_freshness_single_json_matches(patched_client: Any) -> None:
    payload = {
        "asset_id": "abc",
        "qualified_name": "public.orders",
        "status": "fresh",
        "is_stale": False,
        "hours_since_update": 0.5,
        "staleness_threshold_hours": 24,
        "last_update_time": "2026-04-17T10:00:00Z",
        "checked_at": "2026-04-17T10:30:00Z",
    }
    patched_client({"freshness.check": payload})
    result = _run(check_freshness(asset_id="abc"))
    text, _ = _split(result)
    assert text == json.dumps(payload, default=str)


def test_check_freshness_stale_only_uses_list_path(patched_client: Any) -> None:
    stale_rows = [
        {
            "qualified_name": "public.orders",
            "status": "stale",
            "is_stale": True,
            "hours_since_update": 48.5,
            "staleness_threshold_hours": 24,
        }
    ]
    patched_client({"freshness.list": stale_rows})
    result = _run(check_freshness(asset_id="abc", stale_only=True))
    text, _ = _split(result)
    assert text == json.dumps(stale_rows, default=str)


def test_list_schema_changes_json_matches(patched_client: Any) -> None:
    changes = [
        {
            "id": "1",
            "asset_id": "a",
            "qualified_name": "public.orders",
            "change_type": "column_added",
            "severity": "info",
            "column_name": "email",
            "old_value": None,
            "new_value": "text",
            "detected_at": "2026-04-17T10:00:00Z",
            "acknowledged": False,
        }
    ]
    patched_client({"schema.changes": changes})
    result = _run(list_schema_changes())
    text, _ = _split(result)
    assert text == json.dumps(changes, default=str)


def test_health_summary_json_matches(patched_client: Any) -> None:
    payload = {
        "overall_status": "warning",
        "alerts": {"active_count": 3},
        "freshness": {
            "freshness_rate": 85.5,
            "stale_count": 2,
            "total_assets": 14,
        },
        "schema_drift": {"critical_count": 1, "unacknowledged": 3},
        "needs_attention": [{"severity": "critical", "title": "orders stale"}],
        "generated_at": "2026-04-17T15:00:00Z",
    }
    patched_client({"health.summary": payload})
    result = _run(health_summary())
    text, _ = _split(result)
    assert text == json.dumps(payload, default=str)


def test_get_lineage_graph_json_matches(patched_client: Any) -> None:
    graph = {
        "root": {"qualified_name": "public.orders", "name": "orders"},
        "upstream": [{"qualified_name": "raw.orders_source"}],
        "downstream": [{"qualified_name": "mart.order_totals"}],
        "edges": [{"source": "raw.orders_source", "target": "public.orders"}],
    }
    patched_client({"lineage.get": graph})
    result = _run(get_lineage(asset_id="abc"))
    text, _ = _split(result)
    assert text == json.dumps(graph, default=str)


def test_get_lineage_list_all_uses_list_path(patched_client: Any) -> None:
    flat = [
        {"source": "raw.orders_source", "target": "public.orders"},
        {"source": "public.orders", "target": "mart.order_totals"},
    ]
    patched_client({"lineage.list": flat})
    result = _run(get_lineage(asset_id="abc", list_all=True))
    text, _ = _split(result)
    assert text == json.dumps(flat, default=str)


def test_pydantic_model_payloads_survive_normalization(
    patched_client: Any,
) -> None:
    """If the SDK returns Pydantic models, ``to_plain`` must normalize them
    before JSON serialization. The resulting JSON must still be valid."""

    class _FakeModel:
        def __init__(self, data: dict) -> None:
            self._data = data

        def model_dump(self) -> dict:
            return self._data

    data = {"total_assets": 5, "fresh_count": 5, "freshness_rate": 100.0}
    patched_client({"freshness.summary": _FakeModel(data)})
    result = _run(get_freshness_summary())
    text, _ = _split(result)
    assert json.loads(text) == data
