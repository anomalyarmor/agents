#!/usr/bin/env python3
"""Validate version consistency across package files.

Every file that declares an armor-mcp version must agree. The workflow
in `.github/workflows/auto-release.yml` relies on this script as a
pre-release guardrail; drift between any two files here would let a bad
release slip through, so keep the list exhaustive.
"""

import json
import sys
import tomllib
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent.parent

    # Read pyproject.toml (the canonical source; PyPI installs consume this).
    pyproject_path = root / "armor-mcp" / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    pyproject_version = pyproject["project"]["version"]

    # Read .claude-plugin/marketplace.json (both top-level + plugin entry).
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    with open(marketplace_path) as f:
        marketplace = json.load(f)
    marketplace_version = marketplace["version"]
    plugin_version = marketplace["plugins"][0]["version"]

    # Read armor-mcp/server.json (both top-level + first package entry). The
    # MCP Registry reads this; drift here makes the registry claim a
    # different version than PyPI ships.
    server_path = root / "armor-mcp" / "server.json"
    with open(server_path) as f:
        server = json.load(f)
    server_version = server.get("version")
    packages = server.get("packages") or []
    server_package_version = (
        packages[0].get("version")
        if packages and isinstance(packages[0], dict)
        else None
    )

    # Collect every version we know about, keyed by a human-readable path
    # so the mismatch report points to the file the operator needs to fix.
    versions: dict[str, str | None] = {
        "armor-mcp/pyproject.toml [project.version]": pyproject_version,
        ".claude-plugin/marketplace.json [.version]": marketplace_version,
        ".claude-plugin/marketplace.json [.plugins[0].version]": plugin_version,
        "armor-mcp/server.json [.version]": server_version,
        "armor-mcp/server.json [.packages[0].version]": server_package_version,
    }

    # pyproject.toml is the source of truth: it's what gets uploaded to PyPI
    # and what pip install resolves. Every other file must match it.
    errors: list[str] = []
    for label, value in versions.items():
        if value is None:
            errors.append(f"{label} is missing or unreadable")
            continue
        if value != pyproject_version:
            errors.append(
                f"{label}={value} does not match pyproject.toml={pyproject_version}"
            )

    if errors:
        print("Version consistency check FAILED:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print(f"Version consistency check PASSED: {pyproject_version}")
    sys.exit(0)


if __name__ == "__main__":
    main()
