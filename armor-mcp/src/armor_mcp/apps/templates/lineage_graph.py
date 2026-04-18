"""Lineage graph render template.

Input: ``LineageGraph`` dict from ``get_lineage`` with ``root``,
``upstream``, ``downstream``, ``edges``.

Renders as a three-column HTML grid (upstream | root | downstream). No
chart library; a DAG SVG inside an MCP App sandbox is too CSP-heavy and
readability drops below 4 nodes anyway.
"""

from __future__ import annotations

import html
from typing import Any

TITLE = "AnomalyArmor — Lineage"


def html_body(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "<h1>Lineage</h1>" '<p class="caption">Unrecognized lineage payload.</p>'

    # ``get_lineage(list_all=True)`` returns a flat list via
    # ``client.lineage.list``; ``.get`` returns a ``LineageGraph``. If a
    # caller hands us the flat shape we still want something useful.
    if isinstance(payload.get("items"), list) and "root" not in payload:
        return _render_flat(payload["items"])

    root = payload.get("root") or {}
    upstream = payload.get("upstream") or []
    downstream = payload.get("downstream") or []
    edges = payload.get("edges") or []

    if not isinstance(upstream, list):
        upstream = []
    if not isinstance(downstream, list):
        downstream = []

    root_name = html.escape(
        str(root.get("qualified_name") or root.get("name") or "(root)")
    )
    up_col = _column(upstream, align="right") or '<p class="caption">No upstream.</p>'
    down_col = (
        _column(downstream, align="left") or '<p class="caption">No downstream.</p>'
    )
    edge_count = len(edges) if isinstance(edges, list) else 0

    return f"""
<h1>Lineage — {root_name}</h1>
<p class="caption">{len(upstream)} upstream, {len(downstream)} downstream, {edge_count} edge{'s' if edge_count != 1 else ''}.</p>
<div class="lineage">
  <div class="lineage-col">{up_col}</div>
  <div class="lineage-center">→ {root_name} →</div>
  <div class="lineage-col">{down_col}</div>
</div>
""".strip()


def _column(nodes: list, align: str) -> str:
    if not nodes:
        return ""
    items = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = html.escape(
            str(node.get("qualified_name") or node.get("name") or "(unnamed)")
        )
        source = html.escape(
            str(node.get("source_type") or node.get("asset_type") or "")
        )
        source_marker = f' <span class="caption">{source}</span>' if source else ""
        items.append(
            f'    <div class="lineage-node" style="text-align:{align}">{name}{source_marker}</div>'
        )
    return "\n".join(items)


def _render_flat(items: list) -> str:
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        upstream = html.escape(
            str(item.get("upstream_qualified_name") or item.get("source") or "—")
        )
        downstream = html.escape(
            str(item.get("downstream_qualified_name") or item.get("target") or "—")
        )
        edge_type = html.escape(
            str(item.get("edge_type") or item.get("relationship") or "data_flow")
        )
        rows.append(
            f"    <tr><td>{upstream}</td><td>{edge_type}</td><td>{downstream}</td></tr>"
        )
    body = (
        "\n".join(rows)
        if rows
        else '    <tr><td colspan="3">No lineage edges.</td></tr>'
    )
    return f"""
<h1>Lineage (flat)</h1>
<table class="armor-table">
  <thead><tr><th>Upstream</th><th>Edge</th><th>Downstream</th></tr></thead>
  <tbody>
{body}
  </tbody>
</table>
""".strip()
