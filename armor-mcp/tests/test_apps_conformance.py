"""Conformance sweep for MCP Apps (``ui://``) resources.

Each flagship template is rendered against a representative payload and
checked against the invariants the host sandbox + our security model
demand:

- ``mimeType == "text/html"``
- body starts with ``<!DOCTYPE html>``
- ``color-scheme`` meta present (so light/dark themes work)
- CSP equals the constant exported from ``runner.py`` (single chokepoint)
- URI matches ``ui://armor/<template>/<12 hex>``
- no ``aa_live_*``, ``Bearer ``, or email substring leaks into the HTML
  (templates inject only pre-filtered payload data — this catches a
  future footgun where someone passes a raw auth header into a payload)

Also exercises ``render_app`` at the edges:

- unknown template name raises ``ValueError`` with a helpful message
- identical payloads produce identical URIs (URI stability contract)
- payload ordering doesn't matter for the digest
"""

from __future__ import annotations

import re

import pytest
from armor_mcp.apps.runner import CSP_HEADER, render_app
from mcp.types import EmbeddedResource

_URI_RE = re.compile(r"^ui://armor/[a-z_]+/[0-9a-f]{12}$")
_SECRET_PATTERNS = (
    r"aa_live_[A-Za-z0-9_-]+",
    r"Bearer\s+[A-Za-z0-9_\-\.]+",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
)

FLAGSHIP_PAYLOADS = {
    "freshness_timeline_summary": (
        "freshness_timeline",
        {
            "total_assets": 10,
            "fresh_count": 7,
            "stale_count": 2,
            "unknown_count": 1,
            "disabled_count": 0,
            "freshness_rate": 70.0,
        },
    ),
    "freshness_timeline_single": (
        "freshness_timeline",
        {
            "asset_id": "a",
            "qualified_name": "public.orders",
            "status": "stale",
            "is_stale": True,
            "hours_since_update": 48.5,
            "staleness_threshold_hours": 24,
            "last_update_time": "2026-04-15T10:00:00Z",
            "checked_at": "2026-04-17T10:00:00Z",
        },
    ),
    "freshness_timeline_list": (
        "freshness_timeline",
        [
            {
                "qualified_name": "public.orders",
                "status": "stale",
                "is_stale": True,
                "hours_since_update": 48.5,
                "staleness_threshold_hours": 24,
            },
            {
                "qualified_name": "public.users",
                "status": "fresh",
                "is_stale": False,
                "hours_since_update": 1.2,
                "staleness_threshold_hours": 24,
            },
        ],
    ),
    "schema_diff_changes": (
        "schema_diff",
        [
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
        ],
    ),
    "schema_diff_summary": (
        "schema_diff",
        {
            "total_changes": 5,
            "unacknowledged": 3,
            "critical_count": 1,
            "warning_count": 2,
            "info_count": 2,
            "last_check": "2026-04-17T10:00:00Z",
        },
    ),
    "lineage_graph_full": (
        "lineage_graph",
        {
            "root": {"qualified_name": "public.orders", "name": "orders"},
            "upstream": [{"qualified_name": "raw.orders_source"}],
            "downstream": [{"qualified_name": "mart.order_totals"}],
            "edges": [{"source": "raw.orders_source", "target": "public.orders"}],
        },
    ),
    "health_summary_full": (
        "health_summary",
        {
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
        },
    ),
}


@pytest.mark.parametrize(
    "template_name,payload",
    list(FLAGSHIP_PAYLOADS.values()),
    ids=list(FLAGSHIP_PAYLOADS.keys()),
)
def test_resource_shape_is_conformant(template_name: str, payload: object) -> None:
    resource = render_app(template_name, payload)

    assert isinstance(resource, EmbeddedResource)
    assert resource.type == "resource"
    assert resource.resource.mimeType == "text/html"

    html = resource.resource.text
    assert html.startswith("<!DOCTYPE html>"), "missing HTML5 doctype"
    assert 'name="color-scheme"' in html, "missing color-scheme meta"
    assert CSP_HEADER in html, "CSP does not match the single-source constant"
    assert "<html" in html and "</html>" in html

    uri = str(resource.resource.uri)
    assert _URI_RE.match(uri), f"URI does not match ui:// pattern: {uri}"


@pytest.mark.parametrize(
    "template_name,payload",
    list(FLAGSHIP_PAYLOADS.values()),
    ids=list(FLAGSHIP_PAYLOADS.keys()),
)
def test_no_secret_substrings(template_name: str, payload: object) -> None:
    resource = render_app(template_name, payload)
    html = resource.resource.text
    for pattern in _SECRET_PATTERNS:
        matches = re.findall(pattern, html)
        assert not matches, (
            f"template {template_name} leaked a secret-shaped substring "
            f"matching {pattern}: {matches[:3]}"
        )


def test_unknown_template_raises_valueerror() -> None:
    with pytest.raises(ValueError, match="unknown template"):
        render_app("not_a_real_template", {})


def test_identical_payloads_produce_identical_uris() -> None:
    payload = {"total_assets": 1, "fresh_count": 1, "freshness_rate": 100.0}
    r1 = render_app("freshness_timeline", payload)
    r2 = render_app("freshness_timeline", payload)
    assert str(r1.resource.uri) == str(r2.resource.uri)


def test_payload_key_order_does_not_affect_uri() -> None:
    a = {"total_assets": 1, "fresh_count": 1, "freshness_rate": 100.0}
    b = {"freshness_rate": 100.0, "fresh_count": 1, "total_assets": 1}
    assert str(render_app("freshness_timeline", a).resource.uri) == str(
        render_app("freshness_timeline", b).resource.uri
    )


def test_kebab_and_snake_case_resolve_to_same_template() -> None:
    payload = {"total_assets": 1, "fresh_count": 1, "freshness_rate": 100.0}
    snake = render_app("freshness_timeline", payload)
    kebab = render_app("freshness-timeline", payload)
    # Bodies match (same template); URIs differ (template_name is part of URI).
    assert snake.resource.text == kebab.resource.text


def test_freshness_empty_list_skips_vega_cdn() -> None:
    """Regression: empty/single payloads must NOT load the Vega CDN.

    ``vega_lite_spec`` returns ``None`` for empty lists; before the fix the
    runner gated CDN loading on ``callable(spec)``, so the bootstrap still
    ran with ``vegaEmbed(el, null, ...)`` and threw a host-visible error.
    """
    html = render_app("freshness_timeline", []).resource.text
    assert "vega@5" not in html, "Vega CDN loaded for an empty payload"
    assert "vegaEmbed" not in html, "Vega bootstrap shipped with null spec"


def test_lineage_flat_list_payload_renders() -> None:
    """Regression: ``get_lineage(list_all=True)`` returns a flat list.

    Before the fix, the top-level dict guard rejected list payloads and
    every flat-shape call rendered "Unrecognized lineage payload."
    """
    payload = [
        {
            "upstream_qualified_name": "raw.events",
            "downstream_qualified_name": "stg.events",
            "edge_type": "data_flow",
        }
    ]
    html = render_app("lineage_graph", payload).resource.text
    assert "Unrecognized lineage payload" not in html
    assert "raw.events" in html
    assert "stg.events" in html


def test_script_close_tag_in_payload_is_escaped() -> None:
    """Regression: a payload value containing ``</script>`` must not terminate
    the data island. ``_escape_json_for_script`` replaces ``<`` with ``\\u003c``
    so the JSON stays valid and the HTML parser can't be confused."""
    payload = [
        {
            "qualified_name": "public.</script><script>alert(1)</script>",
            "status": "fresh",
        }
    ]
    html = render_app("freshness_timeline", payload).resource.text
    # The literal injection string is gone from the JSON data block.
    assert "</script><script>alert" not in html
