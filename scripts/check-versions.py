#!/usr/bin/env python3
"""Validate version consistency across package files."""

import json
import sys
import tomllib
from pathlib import Path


def main():
    root = Path(__file__).parent.parent

    # Read pyproject.toml version
    pyproject_path = root / "armor-mcp" / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    pyproject_version = pyproject["project"]["version"]

    # Read marketplace.json version
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    with open(marketplace_path) as f:
        marketplace = json.load(f)
    marketplace_version = marketplace["version"]
    plugin_version = marketplace["plugins"][0]["version"]

    # Check consistency
    errors = []
    if pyproject_version != marketplace_version:
        errors.append(
            f"Version mismatch: pyproject.toml={pyproject_version}, "
            f"marketplace.json={marketplace_version}"
        )
    if pyproject_version != plugin_version:
        errors.append(
            f"Version mismatch: pyproject.toml={pyproject_version}, "
            f"plugin version={plugin_version}"
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
