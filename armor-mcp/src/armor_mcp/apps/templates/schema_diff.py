"""Schema diff render template.

Input: list of ``SchemaChange`` dicts from ``list_schema_changes`` OR a
``SchemaSummary`` dict from ``get_schema_summary``. Always renders as
HTML/CSS only; no Vega-Lite needed.
"""

from __future__ import annotations

import html
from typing import Any

TITLE = "AnomalyArmor — Schema drift"


_SEVERITY_PILL = {
    "critical": "pill-err",
    "warning": "pill-warn",
    "info": "pill-ok",
}

_CHANGE_ROW_CLASS = {
    "column_added": "row-add",
    "column_dropped": "row-drop",
    "column_removed": "row-drop",
    "column_renamed": "row-change",
    "column_type_changed": "row-change",
    "type_changed": "row-change",
    "table_added": "row-add",
    "table_dropped": "row-drop",
    "table_removed": "row-drop",
}


def html_body(payload: Any) -> str:
    if isinstance(payload, dict) and "total_changes" in payload:
        return _render_summary(payload)
    if isinstance(payload, list):
        return _render_changes(payload)
    if isinstance(payload, dict) and "changes" in payload:
        return _render_changes(payload["changes"] or [])
    return (
        "<h1>Schema drift</h1>"
        '<p class="caption">No schema changes in this payload.</p>'
    )


def _render_summary(payload: dict) -> str:
    # ``or 0`` handles both missing keys AND explicit None values (Pydantic
    # ``model_dump()`` serializes optional fields as None, which crashes
    # bare ``int()``). See freshness_timeline.py for the same pattern.
    total = int(payload.get("total_changes") or 0)
    unack = int(payload.get("unacknowledged") or 0)
    crit = int(payload.get("critical_count") or 0)
    warn = int(payload.get("warning_count") or 0)
    info = int(payload.get("info_count") or 0)
    last = html.escape(str(payload.get("last_check") or "—"))
    return f"""
<h1>Schema drift summary</h1>
<p class="caption">Last check {last}.</p>
<div class="stat-grid">
  <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">{total}</div></div>
  <div class="stat-card"><div class="stat-label">Unacked</div><div class="stat-value" style="color:var(--accent)">{unack}</div></div>
  <div class="stat-card"><div class="stat-label">Critical</div><div class="stat-value" style="color:var(--err)">{crit}</div></div>
  <div class="stat-card"><div class="stat-label">Warning</div><div class="stat-value" style="color:var(--warn)">{warn}</div></div>
  <div class="stat-card"><div class="stat-label">Info</div><div class="stat-value" style="color:var(--ok)">{info}</div></div>
</div>
""".strip()


def _render_changes(changes: list) -> str:
    count = len(changes)
    if count == 0:
        return "<h1>Schema drift</h1>" '<p class="caption">No changes detected.</p>'
    rows = "\n".join(_change_row(c) for c in changes if isinstance(c, dict))
    return f"""
<h1>Schema changes ({count})</h1>
<table class="armor-table">
  <thead>
    <tr>
      <th>Table</th><th>Column</th><th>Change</th><th>Before</th><th>After</th>
      <th>Severity</th><th>Detected</th><th>Ack</th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
""".strip()


def _optional_str(value: Any) -> str:
    """Render an optional payload value as a string with a None fallback.

    Replaces the older ``str(value) or "—"`` idiom which collapsed any
    falsy-but-real value (``0``, ``False``, ``""``) to the placeholder.
    """
    if value is None:
        return "—"
    return str(value)


def _change_row(change: dict) -> str:
    change_type = str(change.get("change_type", "unknown"))
    row_class = _CHANGE_ROW_CLASS.get(change_type, "row-change")
    qn = html.escape(str(change.get("qualified_name", "—")))
    column = html.escape(_optional_str(change.get("column_name")))
    # `or "—"` would mask falsy-but-real values like 0 or False (e.g., a
    # column default flipping from 0 to 1). Distinguish "missing" from
    # "falsy" via an explicit None check.
    old_value = html.escape(_optional_str(change.get("old_value")))
    new_value = html.escape(_optional_str(change.get("new_value")))
    severity = str(change.get("severity", "info"))
    pill_class = _SEVERITY_PILL.get(severity, "pill-warn")
    detected = html.escape(str(change.get("detected_at") or "—"))
    acked = "✓" if change.get("acknowledged") else "—"
    return (
        f'    <tr class="{row_class}"><td>{qn}</td><td>{column}</td>'
        f"<td>{html.escape(change_type)}</td><td>{old_value}</td><td>{new_value}</td>"
        f'<td><span class="pill {pill_class}">{html.escape(severity)}</span></td>'
        f"<td>{detected}</td><td>{acked}</td></tr>"
    )
