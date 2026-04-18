"""Template modules for MCP Apps (``ui://``) resources.

Each module in this package exports:

- ``TITLE`` (str, optional): ``<title>`` for the rendered page.
- ``html_body(payload: dict) -> str`` (required): the template-specific
  markup that goes inside ``<body>`` before the Vega-Lite scripts.
- ``vega_lite_spec(payload: dict) -> dict`` (optional): if present, the
  runner loads Vega-Lite and calls ``vegaEmbed`` with this spec. Omit
  for table/stat-card templates that need no chart library.
"""
