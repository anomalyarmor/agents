# Releasing armor-mcp

This document describes how to release new versions of the `armor-mcp` package to PyPI.

## Prerequisites

Before your first release, ensure these one-time setup steps are complete:

### 1. PyPI Project Setup

1. Create the `armor-mcp` project on [PyPI](https://pypi.org/)
2. Configure Trusted Publishing:
   - Go to Project Settings > Publishing
   - Add publisher:
     - Owner: `anomalyarmor`
     - Repository: `agents`
     - Workflow: `publish-pypi.yml`
     - Environment: `pypi`

### 2. TestPyPI Setup (optional but recommended)

1. Create the `armor-mcp` project on [TestPyPI](https://test.pypi.org/)
2. Configure Trusted Publishing with environment: `testpypi`

### 3. GitHub Environments

Create two environments in GitHub repository settings:

- `pypi` - For production PyPI releases
- `testpypi` - For test releases

### 4. `RELEASE_PAT` secret (required for the auto-release chain)

GitHub deliberately suppresses workflow triggers from events created by `GITHUB_TOKEN` (to prevent infinite recursion). That means a release created by `auto-release.yml` using `GITHUB_TOKEN` would **not** fire the `release.types: [published]` listener on `publish-pypi.yml`, silently breaking the publish chain. The workaround is a Personal Access Token:

1. Create a classic PAT at <https://github.com/settings/tokens/new> with `repo` scope and an expiration you can stomach (12 months is common — set a calendar reminder to rotate).
2. Add it at <https://github.com/anomalyarmor/agents/settings/secrets/actions/new> as `RELEASE_PAT`.
3. The workflow uses `secrets.RELEASE_PAT || secrets.GITHUB_TOKEN` so the release still gets created if the PAT is missing, but it will print a loud `::warning::` telling you to trigger `publish-pypi.yml` by hand.

## Version Management

Versions must be consistent across:

- `armor-mcp/pyproject.toml` - Package version
- `.claude-plugin/marketplace.json` - Plugin metadata

The CI runs `scripts/check-versions.py` to verify consistency.

## Release Process

### Production Release (automated)

Bump the version in a PR, merge, done. The `auto-release.yml` workflow watches `main` for version-bump commits and creates the tag + GitHub release, which then triggers `publish-pypi.yml` to push to PyPI.

1. Update the version in all three places:
   ```bash
   # armor-mcp/pyproject.toml
   version = "X.Y.Z"

   # armor-mcp/server.json
   "version": "X.Y.Z",

   # .claude-plugin/marketplace.json (both top-level and plugins[0])
   "version": "X.Y.Z"
   ```

2. Commit, push, and merge the PR:
   ```bash
   git commit -am "chore: bump version to X.Y.Z"
   ```

3. After merge to `main`:
   - `auto-release.yml` detects the version bump, verifies consistency via `scripts/check-versions.py`, creates tag `vX.Y.Z` + a GitHub release with auto-generated notes.
   - That release fires `publish-pypi.yml`, which re-runs version checks, builds, and publishes to PyPI.

If the same version is merged twice (e.g. after a revert), `auto-release.yml` skips silently instead of erroring — it's idempotent on version number.

### Testing with TestPyPI

1. Go to Actions > "Publish armor-mcp to PyPI"
2. Click "Run workflow"
3. Enter the version (e.g., `0.1.0`)
4. Optionally enable "Dry run" to preview without publishing
5. Click "Run workflow"

### Manual release (fallback)

If `auto-release.yml` is disabled or you need to re-release an existing version:

1. Update the version (same as step 1 above), commit, push.
2. Create a GitHub release manually: tag `vX.Y.Z`, title `vX.Y.Z`, auto-generate notes.
3. `publish-pypi.yml` picks it up the same way.

## Recovery

**Release was auto-created but didn't reach PyPI (RELEASE_PAT wasn't set):**

`auto-release.yml` will print a `::warning::` in this case. The fix is a two-step dance because GitHub won't re-fire the release event for a release that already exists:

1. Set up `RELEASE_PAT` per [Prerequisites](#prerequisites).
2. Delete the orphaned release + tag:
   ```bash
   gh release delete vX.Y.Z --yes --cleanup-tag
   ```
3. Re-run `auto-release.yml` manually:
   ```bash
   gh workflow run auto-release.yml
   ```
   The idempotency check now sees no existing release, creates one using `RELEASE_PAT`, and `publish-pypi.yml` fires on the release event and publishes to PyPI.

**Do not** run `gh workflow run publish-pypi.yml`. That path publishes to TestPyPI (`workflow_dispatch` → `publish-testpypi` job), not real PyPI (`publish-pypi` only fires on the `release` event).

## Troubleshooting

### Version mismatch error

```
Version mismatch: pyproject.toml=X.Y.Z, marketplace.json=A.B.C
```

Ensure both files have the same version before releasing.

### Trusted Publisher not configured

```
Error: OpenID Connect token exchange failed
```

Verify Trusted Publishing is configured in PyPI project settings with the correct:
- Repository owner/name
- Workflow filename
- Environment name

### Package already exists

```
Error: File already exists
```

You cannot overwrite an existing version on PyPI. Bump the version number.
