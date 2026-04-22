#!/usr/bin/env python3
"""Authentication validation hook for AnomalyArmor skills.

Runs as a PreToolUse:Bash hook before every skill Bash call. Exit 0 = proceed;
exit 1 = block the call with a message to stderr.

Resolution order:

1. **Real user key.** ``ARMOR_API_KEY`` env var (``aa_live_*``/``aa_test_*``) or
   an ``api_key`` field in ``~/.armor/config.yaml``. Pass through silently.
2. **Cached demo session.** ``~/.armor/.demo-session.json`` with an unexpired
   ``aa_demo_*`` key (TECH-978.3). The AnomalyArmor SDK reads this file as a
   last-resort fallback, so we do not need to propagate env vars across the
   hook → Bash boundary.
3. **Mint a new demo session.** Fall back to ``POST {ARMOR_API_URL}/demo/session``
   (default ``https://app.anomalyarmor.ai/api/v1/demo/session``), write the
   returned key + ``expires_at`` to ``~/.armor/.demo-session.json``, print a
   one-line banner to stderr, and exit 0.
4. **Fail closed.** If the mint endpoint is unreachable, print setup guidance
   and exit 1 so Claude sees a clear error rather than an opaque auth failure
   mid-skill.

Exit codes:
    0 - Authentication configured and valid (or demo session active).
    1 - No authentication, and demo fallback failed.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Key format patterns.
USER_KEY_PATTERN = re.compile(r"^aa_(live|test)_[a-zA-Z0-9]{32,}$")
DEMO_KEY_PATTERN = re.compile(r"^aa_demo_[a-zA-Z0-9]{32,}$")

# Cached demo-session path. Matches what the SDK's
# anomalyarmor.config.load_demo_session_key() reads.
DEMO_SESSION_PATH = Path.home() / ".armor" / ".demo-session.json"

# Default API base. Override with ARMOR_API_URL for local or staging.
DEFAULT_API_URL = "https://app.anomalyarmor.ai/api/v1"

DEMO_MINT_TIMEOUT_SECONDS = 10


def _log(msg: str) -> None:
    """Banner messages always go to stderr so they don't pollute skill output."""
    print(msg, file=sys.stderr)


def _config_yaml_api_key() -> str | None:
    """Tiny YAML parser: just the ``api_key:`` line in ``~/.armor/config.yaml``."""
    config_path = Path.home() / ".armor" / "config.yaml"
    if not config_path.exists():
        return None
    try:
        for raw in config_path.read_text().splitlines():
            line = raw.strip()
            if line.startswith("api_key:"):
                value = line.split(":", 1)[1].strip().strip("'\"")
                return value or None
    except OSError:
        return None
    return None


def _cached_demo_session_valid() -> bool:
    """True iff ``~/.armor/.demo-session.json`` has an unexpired ``aa_demo_*`` key."""
    if not DEMO_SESSION_PATH.exists():
        return False
    try:
        payload = json.loads(DEMO_SESSION_PATH.read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False

    key = payload.get("api_key")
    expires_at_raw = payload.get("expires_at")
    if not isinstance(key, str) or not DEMO_KEY_PATTERN.match(key):
        return False
    if not isinstance(expires_at_raw, str):
        return False
    try:
        expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def _mint_demo_session(api_url: str) -> tuple[str, str] | None:
    """POST to /demo/session; return (api_key, expires_at) or None on failure.

    Keeps the request deliberately small — no retry loop, no exponential
    backoff. If the call fails (offline, endpoint down, rate limited), we
    surface the original setup guidance so a cold prospect knows what to do.
    """
    endpoint = api_url.rstrip("/") + "/demo/session"
    try:
        req = urllib.request.Request(
            endpoint,
            data=b"",
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(
            req, timeout=DEMO_MINT_TIMEOUT_SECONDS, context=ctx
        ) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None

    try:
        payload = json.loads(body)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None

    # AnomalyArmor APIs wrap successful responses as
    # ``{"success": true, "data": {...}}``. Unwrap if present, else fall back
    # to the raw payload for forward compatibility with a simpler response
    # shape.
    data: object = payload.get("data") if "data" in payload else payload
    if not isinstance(data, dict):
        return None

    key = data.get("api_key")
    expires_at = data.get("expires_at")
    if not isinstance(key, str) or not DEMO_KEY_PATTERN.match(key):
        return None
    if not isinstance(expires_at, str):
        return None
    return key, expires_at


def _cache_demo_session(api_key: str, expires_at: str) -> None:
    """Write the demo session to disk with 0600 perms."""
    DEMO_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEMO_SESSION_PATH.write_text(
        json.dumps({"api_key": api_key, "expires_at": expires_at}, indent=2)
    )
    try:
        DEMO_SESSION_PATH.chmod(0o600)
    except OSError:
        # Non-POSIX filesystem; not worth failing over.
        pass


def _print_setup_guidance() -> None:
    """Original error message for when demo fallback also fails."""
    _log("Error: No AnomalyArmor API key configured.")
    _log("")
    _log("To configure authentication:")
    _log("")
    _log("Option 1: Set environment variable")
    _log("  export ARMOR_API_KEY=aa_live_your_key_here")
    _log("")
    _log("Option 2: Create config file")
    _log("  mkdir -p ~/.armor")
    _log("  echo 'api_key: aa_live_your_key_here' > ~/.armor/config.yaml")
    _log("")
    _log("Get your API key at: https://app.anomalyarmor.ai/settings/api-keys")


def main() -> int:
    """Main entry point."""
    # 1. Real user key via env or config.yaml.
    env_key = os.environ.get("ARMOR_API_KEY")
    if env_key:
        if USER_KEY_PATTERN.match(env_key):
            return 0
        _log("Error: Invalid API key format in ARMOR_API_KEY environment variable.")
        _log("API keys should match pattern: aa_live_* or aa_test_*")
        _log("Get a valid key at: https://app.anomalyarmor.ai/settings/api-keys")
        return 1

    file_key = _config_yaml_api_key()
    if file_key:
        if USER_KEY_PATTERN.match(file_key):
            return 0
        _log("Error: Invalid API key format in ~/.armor/config.yaml.")
        _log("API keys should match pattern: aa_live_* or aa_test_*")
        _log("Get a valid key at: https://app.anomalyarmor.ai/settings/api-keys")
        return 1

    # 2. Unexpired cached demo session — let the SDK pick it up silently.
    if _cached_demo_session_valid():
        return 0

    # 3. Mint a new demo session.
    api_url = os.environ.get("ARMOR_API_URL", DEFAULT_API_URL)
    minted = _mint_demo_session(api_url)
    if minted is not None:
        api_key, expires_at = minted
        try:
            _cache_demo_session(api_key, expires_at)
        except OSError:
            _log(
                "Warning: Could not write ~/.armor/.demo-session.json; demo key is valid for this invocation only."
            )
        _log("")
        _log("AnomalyArmor demo mode: using a read-only public demo key.")
        _log(f"Key expires at {expires_at}. Sign up for your own account at:")
        _log("  https://app.anomalyarmor.ai/signup")
        _log("")
        return 0

    # 4. All fallbacks failed.
    _print_setup_guidance()
    return 1


if __name__ == "__main__":
    sys.exit(main())
