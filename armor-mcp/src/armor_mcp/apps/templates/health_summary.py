"""Health summary render template.

Input: ``HealthSummary`` dict from ``health_summary`` with
``overall_status``, ``alerts``, ``freshness``, ``schema_drift``,
``needs_attention``, ``generated_at``.
"""

from __future__ import annotations

import html
from typing import Any

TITLE = "AnomalyArmor — Health summary"


_STATUS_PILL = {
    "healthy": "pill-ok",
    "warning": "pill-warn",
    "critical": "pill-err",
}


def html_body(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "<h1>Health</h1>" '<p class="caption">Unrecognized health payload.</p>'

    overall = str(payload.get("overall_status", "unknown"))
    generated = html.escape(str(payload.get("generated_at") or "—"))
    alerts = payload.get("alerts") or {}
    freshness = payload.get("freshness") or {}
    schema = payload.get("schema_drift") or {}
    attention = payload.get("needs_attention") or []

    cards = _stat_cards(alerts, freshness, schema)
    attention_list = _attention_list(attention)
    pill_cls = _STATUS_PILL.get(overall, "pill-warn")

    return f"""
<h1>Data health <span class="pill {pill_cls}">{html.escape(overall)}</span></h1>
<p class="caption">Generated {generated}.</p>
<div class="stat-grid">
{cards}
</div>
{attention_list}
""".strip()


def _stat_cards(alerts: dict, freshness: dict, schema: dict) -> str:
    fresh_rate = freshness.get("freshness_rate") or 0
    stale = int(freshness.get("stale_count") or 0)
    total = int(freshness.get("total_assets") or 0)
    crit = int(schema.get("critical_count") or 0)
    unack = int(schema.get("unacknowledged") or 0)

    # Alerts dict shape varies across SDK versions; prefer common keys
    # and surface a "—" when nothing is populated rather than fabricating.
    # Coerce to int even though the value should already be numeric -- a
    # future SDK shape change could land a string here, and unescaped
    # interpolation under script-src 'unsafe-inline' would let any inline
    # event-handler markup execute.
    active = _first_populated(
        alerts, ("active_count", "triggered_count", "open_count", "total_active")
    )
    try:
        active_display = str(int(active)) if active is not None else "—"
    except (TypeError, ValueError):
        active_display = "—"

    return f"""
  <div class="stat-card">
    <div class="stat-label">Freshness</div>
    <div class="stat-value">{_rate_display(fresh_rate)}</div>
    <div class="caption">{stale}/{total} stale</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Active alerts</div>
    <div class="stat-value" style="color:var(--err)">{active_display}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Schema unacked</div>
    <div class="stat-value" style="color:var(--warn)">{unack}</div>
    <div class="caption">{crit} critical</div>
  </div>
""".rstrip()


def _rate_display(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{numeric:.0f}%"


def _first_populated(source: dict, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return None


def _attention_list(items: list) -> str:
    if not items:
        return '<p class="caption" style="margin-top:16px">Nothing needs attention.</p>'
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "info"))
        pill_cls = _STATUS_PILL.get(severity, "pill-warn")
        title = html.escape(
            str(item.get("title") or item.get("asset_name") or "(untitled)")
        )
        rows.append(
            f'    <tr><td><span class="pill {pill_cls}">{html.escape(severity)}</span></td>'
            f"<td>{title}</td></tr>"
        )
    body = "\n".join(rows) if rows else ""
    # Count rendered rows, not raw input. Non-dict entries are filtered
    # out above, so len(items) overstates what the user actually sees.
    return f"""
<h1 style="font-size:14px;margin-top:20px;margin-bottom:4px">Needs attention ({len(rows)})</h1>
<table class="armor-table">
  <tbody>
{body}
  </tbody>
</table>
""".strip()
