"""Freshness render template.

Accepts the payload shape returned by ``check_freshness`` /
``get_freshness_summary``:

- Single ``FreshnessStatus`` dict (``check_freshness`` default).
- A list of ``FreshnessStatus`` (``check_freshness(stale_only=True)`` or
  ``freshness.list``).
- ``FreshnessSummary`` dict (``get_freshness_summary``).

The template inspects the shape at render time and picks the right view.
Reads data from the injected ``armor-data`` JSON island; all HTML escape
happens in ``html_body``.
"""

from __future__ import annotations

import html
from typing import Any

TITLE = "AnomalyArmor — Freshness"


def _fmt_hours(hours: float | int | None) -> str:
    if hours is None:
        return "—"
    try:
        value = float(hours)
    except (TypeError, ValueError):
        return "—"
    if value < 1:
        return f"{int(value * 60)}m"
    if value < 48:
        return f"{value:.1f}h"
    return f"{value / 24:.1f}d"


def _pill(status: str) -> str:
    mapping = {
        "fresh": "pill-ok",
        "stale": "pill-err",
        "unknown": "pill-warn",
        "disabled": "pill-warn",
    }
    cls = mapping.get(status, "pill-warn")
    return f'<span class="pill {cls}">{html.escape(status)}</span>'


def _is_summary(payload: dict) -> bool:
    return isinstance(payload, dict) and "freshness_rate" in payload


def _is_single_status(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and "qualified_name" in payload
        and "is_stale" in payload
    )


def html_body(payload: Any) -> str:
    if _is_summary(payload):
        return _render_summary(payload)
    if _is_single_status(payload):
        return _render_single(payload)
    if isinstance(payload, list):
        return _render_list(payload)
    return (
        "<h1>Freshness</h1>"
        '<p class="caption">Unrecognized freshness payload shape.</p>'
    )


def _render_summary(payload: dict) -> str:
    # ``dict.get(key, default)`` only returns the default when the key is
    # missing. Pydantic ``model_dump()`` serializes optional fields as
    # explicit ``None``, which then crashes ``int(None)`` and the rate's
    # ``f"{None:.1f}"``. Coerce via ``or 0`` (matches health_summary.py).
    total = int(payload.get("total_assets") or 0)
    fresh = int(payload.get("fresh_count") or 0)
    stale = int(payload.get("stale_count") or 0)
    unknown = int(payload.get("unknown_count") or 0)
    rate = _safe_rate(payload.get("freshness_rate"))
    return f"""
<h1>Freshness summary</h1>
<p class="caption">{total} monitored assets, {rate} fresh.</p>
<div class="stat-grid">
  <div class="stat-card"><div class="stat-label">Fresh</div><div class="stat-value" style="color:var(--ok)">{fresh}</div></div>
  <div class="stat-card"><div class="stat-label">Stale</div><div class="stat-value" style="color:var(--err)">{stale}</div></div>
  <div class="stat-card"><div class="stat-label">Unknown</div><div class="stat-value" style="color:var(--warn)">{unknown}</div></div>
  <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">{total}</div></div>
</div>
<div id="armor-chart"></div>
""".strip()


def _safe_rate(value: Any) -> str:
    """Format a percentage with a None/non-numeric fallback."""
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "—"


def _render_single(payload: dict) -> str:
    qn = html.escape(str(payload.get("qualified_name", "(unknown)")))
    status = str(payload.get("status", "unknown"))
    hours = payload.get("hours_since_update")
    threshold = payload.get("staleness_threshold_hours")
    last_update = html.escape(str(payload.get("last_update_time") or "—"))
    return f"""
<h1>{qn}</h1>
<p class="caption">Last update {last_update}.</p>
<div class="stat-grid">
  <div class="stat-card"><div class="stat-label">Status</div><div class="stat-value">{_pill(status)}</div></div>
  <div class="stat-card"><div class="stat-label">Since update</div><div class="stat-value">{_fmt_hours(hours)}</div></div>
  <div class="stat-card"><div class="stat-label">Threshold</div><div class="stat-value">{_fmt_hours(threshold)}</div></div>
</div>
<noscript><pre>{html.escape(str(payload))}</pre></noscript>
""".strip()


def _render_list(payload: list) -> str:
    rows = "\n".join(_list_row(item) for item in payload)
    count = len(payload)
    return f"""
<h1>Freshness ({count} table{'s' if count != 1 else ''})</h1>
<div id="armor-chart"></div>
<table class="armor-table">
  <thead><tr><th>Table</th><th>Status</th><th>Since update</th><th>Threshold</th></tr></thead>
  <tbody>
{rows}
  </tbody>
</table>
""".strip()


def _list_row(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    qn = html.escape(str(item.get("qualified_name", "(unknown)")))
    status = str(item.get("status", "unknown"))
    hours = _fmt_hours(item.get("hours_since_update"))
    threshold = _fmt_hours(item.get("staleness_threshold_hours"))
    return (
        f"    <tr><td>{qn}</td>"
        f"<td>{_pill(status)}</td>"
        f"<td>{hours}</td>"
        f"<td>{threshold}</td></tr>"
    )


def vega_lite_spec(payload: Any) -> dict | None:
    """Emit a small Vega-Lite bar chart only when we have aggregate counts.

    For single-status and unknown shapes, return None so the runner skips
    the Vega CDN load entirely.
    """
    if _is_summary(payload):
        data = [
            {"status": "fresh", "count": payload.get("fresh_count", 0)},
            {"status": "stale", "count": payload.get("stale_count", 0)},
            {"status": "unknown", "count": payload.get("unknown_count", 0)},
            {"status": "disabled", "count": payload.get("disabled_count", 0)},
        ]
        return _bar_spec(data)
    if isinstance(payload, list) and payload:
        counts: dict[str, int] = {}
        for item in payload:
            if isinstance(item, dict):
                status = str(item.get("status", "unknown"))
                counts[status] = counts.get(status, 0) + 1
        data = [{"status": k, "count": v} for k, v in counts.items()]
        return _bar_spec(data)
    return None


_STATUS_COLORS = {
    "fresh": "#16a34a",
    "stale": "#dc2626",
    "unknown": "#eab308",
    "disabled": "#6b7280",
}


def _bar_spec(data: list[dict]) -> dict:
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": data},
        "mark": {"type": "bar", "cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3},
        "width": "container",
        "height": 200,
        "encoding": {
            "x": {"field": "status", "type": "nominal", "axis": {"labelAngle": 0}},
            "y": {"field": "count", "type": "quantitative", "axis": {"title": None}},
            "color": {
                "field": "status",
                "type": "nominal",
                "scale": {
                    "domain": list(_STATUS_COLORS.keys()),
                    "range": list(_STATUS_COLORS.values()),
                },
                "legend": None,
            },
        },
        "config": {"background": "transparent", "view": {"stroke": None}},
    }
