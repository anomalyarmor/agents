#!/usr/bin/env python3
"""Authentication validation hook for AnomalyArmor skills.

This script validates that the user has configured their AnomalyArmor API key
before any skill can execute. It checks:
1. ARMOR_API_KEY environment variable
2. ~/.armor/config.yaml configuration file

If no valid configuration is found, it exits with a clear error message
and instructions for setup.

Usage:
    python scripts/ensure-auth.py

Exit codes:
    0 - Authentication configured and valid
    1 - No authentication configured
"""

import os
import re
import sys
from pathlib import Path

# API key pattern: aa_live_* or aa_test_*
API_KEY_PATTERN = re.compile(r"^aa_(live|test)_[a-zA-Z0-9]{32,}$")


def get_api_key_from_env() -> str | None:
    """Get API key from environment variable."""
    return os.environ.get("ARMOR_API_KEY")


def get_api_key_from_config() -> str | None:
    """Get API key from ~/.armor/config.yaml."""
    config_path = Path.home() / ".armor" / "config.yaml"
    if not config_path.exists():
        return None

    try:
        # Simple YAML parsing for api_key field
        content = config_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("api_key:"):
                # Extract value after colon, strip quotes
                value = line.split(":", 1)[1].strip()
                value = value.strip("'\"")
                return value if value else None
    except Exception:
        return None

    return None


def validate_api_key(key: str) -> bool:
    """Validate API key format."""
    return bool(API_KEY_PATTERN.match(key))


def main() -> int:
    """Main entry point."""
    # Check environment variable first (takes precedence)
    api_key = get_api_key_from_env()
    source = "ARMOR_API_KEY environment variable"

    # Fall back to config file
    if not api_key:
        api_key = get_api_key_from_config()
        source = "~/.armor/config.yaml"

    # No API key found
    if not api_key:
        print("Error: No AnomalyArmor API key configured.", file=sys.stderr)
        print("", file=sys.stderr)
        print("To configure authentication:", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 1: Set environment variable", file=sys.stderr)
        print("  export ARMOR_API_KEY=aa_live_your_key_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 2: Create config file", file=sys.stderr)
        print("  mkdir -p ~/.armor", file=sys.stderr)
        print(
            "  echo 'api_key: aa_live_your_key_here' > ~/.armor/config.yaml",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        print(
            "Get your API key at: https://app.anomalyarmor.ai/settings/api-keys",
            file=sys.stderr,
        )
        return 1

    # Validate format
    if not validate_api_key(api_key):
        print(f"Error: Invalid API key format in {source}.", file=sys.stderr)
        print("", file=sys.stderr)
        print("API keys should match pattern: aa_live_* or aa_test_*", file=sys.stderr)
        print(
            "Get a valid key at: https://app.anomalyarmor.ai/settings/api-keys",
            file=sys.stderr,
        )
        return 1

    # Success - authentication is configured
    return 0


if __name__ == "__main__":
    sys.exit(main())
