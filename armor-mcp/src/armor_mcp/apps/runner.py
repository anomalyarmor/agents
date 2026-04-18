"""Shared HTML harness for MCP Apps (``ui://`` resources).

Each ``render_app(template_name, payload)`` call:

1. Looks up the template module under ``apps.templates`` by name.
2. Calls its ``html_body(payload)`` (always) and, for chart templates,
   its ``vega_lite_spec(payload)`` (optional).
3. Wraps the body in a shared HTML5 scaffold: doctype, ``color-scheme``
   meta, CSP, Vega-Lite from jsdelivr, and a single inline bootstrap
   script that reads the injected JSON data + spec and calls
   ``vegaEmbed``.
4. Returns an ``EmbeddedResource`` with a stable URI
   (``ui://armor/<template>/<sha256(payload)[:12]>``) so hosts can cache
   by URI and identical payloads dedupe.

The CSP below is a best-guess for Claude Desktop nightly / Cursor
experimental host sandboxes as of 2026-04-18. If a host rejects it,
narrow the offending directive in this file — all four templates flow
through one scaffold.

Security invariants (enforced by ``tests/test_apps_conformance.py``):
- ``mimeType`` is always ``text/html``.
- The HTML body starts with ``<!DOCTYPE html>``.
- ``color-scheme`` meta is present so light/dark themes work.
- CSP is present and matches ``CSP_HEADER``.
- Output contains no ``aa_live_*`` / ``Bearer `` / email substrings.
  Templates inject only pre-filtered payload data; API tokens never
  reach this layer.
"""

from __future__ import annotations

import importlib
import json
from hashlib import sha256
from typing import Any

from mcp.types import EmbeddedResource, TextResourceContents

# Best-guess CSP for MCP Apps host sandboxes. See module docstring.
# Kept as a single string so the conformance test can assert byte equality.
CSP_HEADER = (
    "default-src 'none'; "
    "script-src 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'unsafe-inline'; "
    "img-src data: blob:; "
    "connect-src 'none'; "
    "font-src data:"
)

# Pinned Vega-Lite + dependencies. Version is frozen so cache hits are
# stable and an upstream breaking change doesn't brick every armor-mcp
# render overnight. Bump intentionally.
_VEGA_LITE_VERSION = "5.17.0"
_VEGA_VERSION = "5.27.0"
_VEGA_EMBED_VERSION = "6.24.0"

_VEGA_SCRIPTS = (
    f'<script src="https://cdn.jsdelivr.net/npm/vega@{_VEGA_VERSION}"></script>\n'
    f'<script src="https://cdn.jsdelivr.net/npm/vega-lite@{_VEGA_LITE_VERSION}"></script>\n'
    f'<script src="https://cdn.jsdelivr.net/npm/vega-embed@{_VEGA_EMBED_VERSION}"></script>'
)

_BOOTSTRAP_SCRIPT = """
<script>
(function () {
  var dataEl = document.getElementById('armor-data');
  var specEl = document.getElementById('armor-spec');
  var chartEl = document.getElementById('armor-chart');
  if (!chartEl || !specEl || !dataEl) return;
  try {
    var spec = JSON.parse(specEl.textContent);
    var data = JSON.parse(dataEl.textContent);
    // Vega-Lite convention: inject rows under `values` on the inline
    // data source if the template doesn't pre-populate them.
    if (spec && spec.data && spec.data.name === 'armor' && Array.isArray(data)) {
      spec.datasets = spec.datasets || {};
      spec.datasets.armor = data;
    }
    vegaEmbed(chartEl, spec, {actions: false, renderer: 'svg'});
  } catch (e) {
    chartEl.textContent = 'chart render failed: ' + (e && e.message ? e.message : e);
  }
})();
</script>
""".strip()

_SCAFFOLD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light dark">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<title>{title}</title>
<style>
  :root {{
    color-scheme: light dark;
    --fg: #1f2937;
    --fg-muted: #6b7280;
    --bg: #ffffff;
    --bg-muted: #f9fafb;
    --border: #e5e7eb;
    --accent: #2563eb;
    --ok: #16a34a;
    --warn: #eab308;
    --err: #dc2626;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --fg: #e5e7eb;
      --fg-muted: #9ca3af;
      --bg: #0f172a;
      --bg-muted: #1e293b;
      --border: #334155;
      --accent: #60a5fa;
      --ok: #4ade80;
      --warn: #facc15;
      --err: #f87171;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    color: var(--fg);
    background: var(--bg);
    margin: 0;
    padding: 16px;
    font-size: 14px;
    line-height: 1.4;
  }}
  h1 {{ font-size: 16px; margin: 0 0 4px 0; }}
  .caption {{ color: var(--fg-muted); font-size: 12px; margin-bottom: 12px; }}
  #armor-chart {{ min-height: 240px; }}
  table.armor-table {{
    border-collapse: collapse;
    width: 100%;
    font-variant-numeric: tabular-nums;
  }}
  table.armor-table th, table.armor-table td {{
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }}
  table.armor-table th {{ color: var(--fg-muted); font-weight: 500; font-size: 12px; }}
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  }}
  .stat-card {{
    background: var(--bg-muted);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }}
  .stat-label {{ color: var(--fg-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }}
  .stat-value {{ font-size: 22px; font-weight: 600; margin-top: 4px; }}
  .pill {{
    display: inline-block;
    padding: 1px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 500;
  }}
  .pill-ok {{ background: color-mix(in srgb, var(--ok) 15%, transparent); color: var(--ok); }}
  .pill-warn {{ background: color-mix(in srgb, var(--warn) 15%, transparent); color: var(--warn); }}
  .pill-err {{ background: color-mix(in srgb, var(--err) 15%, transparent); color: var(--err); }}
  .row-add td:first-child {{ border-left: 3px solid var(--ok); }}
  .row-drop td:first-child {{ border-left: 3px solid var(--err); }}
  .row-change td:first-child {{ border-left: 3px solid var(--warn); }}
  .lineage {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 16px;
    align-items: center;
  }}
  .lineage-col {{ display: flex; flex-direction: column; gap: 6px; }}
  .lineage-node {{
    background: var(--bg-muted);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px;
  }}
  .lineage-center {{ color: var(--accent); font-weight: 600; text-align: center; }}
  noscript {{ color: var(--fg-muted); }}
</style>
</head>
<body>
{body}
{vega_scripts}
<script id="armor-data" type="application/json">{data_json}</script>
<script id="armor-spec" type="application/json">{spec_json}</script>
{bootstrap}
</body>
</html>
"""

_TEMPLATE_PACKAGE = "armor_mcp.apps.templates"


def _load_template(template_name: str) -> Any:
    """Import the template module by name.

    Kept dynamic so adding a 5th template is one new file under
    ``apps/templates/`` without touching ``runner.py``.
    """
    module_name = template_name.replace("-", "_")
    try:
        return importlib.import_module(f"{_TEMPLATE_PACKAGE}.{module_name}")
    except ImportError as exc:
        raise ValueError(
            f"unknown template '{template_name}'. "
            f"Add a module at {_TEMPLATE_PACKAGE}.{module_name} with "
            f"html_body(payload) (required) and vega_lite_spec(payload) "
            f"(optional)."
        ) from exc


def _payload_digest(payload: Any) -> str:
    """Stable 12-char hex digest of the payload for URI cache keys."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()[:12]


def render_app(template_name: str, payload: Any) -> EmbeddedResource:
    """Render a payload through a template and wrap it as EmbeddedResource.

    Args:
        template_name: Template filename (without ``.py``). Supports
            kebab-case at the URI layer; converted to snake_case for the
            Python import. ``"freshness-timeline"`` and
            ``"freshness_timeline"`` both resolve to the same module.
        payload: JSON-serializable data passed unchanged to the
            template's ``html_body`` (and ``vega_lite_spec``, if any).

    Returns:
        An ``EmbeddedResource`` the caller can include in a FastMCP tool's
        content-block list. The URI is stable per ``(template, payload)``.
    """
    module = _load_template(template_name)
    body_html = module.html_body(payload)
    spec = getattr(module, "vega_lite_spec", None)
    spec_json = json.dumps(spec(payload), default=str) if callable(spec) else "null"
    data_json = json.dumps(payload, default=str)
    title = getattr(module, "TITLE", f"AnomalyArmor — {template_name}")

    # If this template doesn't need Vega-Lite, skip the CDN load AND the
    # bootstrap. Keeps table/stat-card renders small and CDN-independent.
    needs_vega = callable(spec)
    vega_scripts = _VEGA_SCRIPTS if needs_vega else ""
    bootstrap = _BOOTSTRAP_SCRIPT if needs_vega else ""

    html = _SCAFFOLD.format(
        csp=CSP_HEADER,
        title=_escape_title(title),
        body=body_html,
        vega_scripts=vega_scripts,
        data_json=_escape_json_for_script(data_json),
        spec_json=_escape_json_for_script(spec_json),
        bootstrap=bootstrap,
    )
    uri = f"ui://armor/{template_name}/{_payload_digest(payload)}"
    return EmbeddedResource(
        type="resource",
        resource=TextResourceContents(
            uri=uri,
            mimeType="text/html",
            text=html,
        ),
    )


def _escape_title(title: str) -> str:
    """Escape title for safe interpolation into ``<title>``.

    Titles come from ``TITLE`` module constants set by us, not from user
    payloads; this is defense-in-depth only.
    """
    return title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_json_for_script(data_json: str) -> str:
    """Escape ``</script>`` and HTML comment openers inside a JSON blob.

    JSON doesn't allow raw ``<`` inside strings without escaping in an
    HTML context. Browsers terminate ``<script>...</script>`` blocks on
    the literal substring ``</script>`` regardless of JSON quoting, so
    any payload value containing that substring would break out of the
    data island. Replace ``<`` with the Unicode escape ``\\u003c`` so
    the JSON stays valid and the HTML parser can't be confused.
    """
    return data_json.replace("<", "\\u003c")
