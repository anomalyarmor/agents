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

## Version Management

Versions must be consistent across:

- `armor-mcp/pyproject.toml` - Package version
- `.claude-plugin/marketplace.json` - Plugin metadata

The CI runs `scripts/check-versions.py` to verify consistency.

## Release Process

### Testing with TestPyPI

1. Go to Actions > "Publish armor-mcp to PyPI"
2. Click "Run workflow"
3. Enter the version (e.g., `0.1.0`)
4. Optionally enable "Dry run" to preview without publishing
5. Click "Run workflow"

### Production Release

1. Update versions in both files:
   ```bash
   # In armor-mcp/pyproject.toml
   version = "X.Y.Z"
   
   # In .claude-plugin/marketplace.json
   "version": "X.Y.Z"
   ```

2. Commit and push:
   ```bash
   git add armor-mcp/pyproject.toml .claude-plugin/marketplace.json
   git commit -m "chore: bump version to X.Y.Z"
   git push
   ```

3. Create a GitHub Release:
   - Go to Releases > "Create a new release"
   - Tag: `vX.Y.Z` (e.g., `v0.1.0`)
   - Title: `vX.Y.Z`
   - Description: Release notes
   - Click "Publish release"

4. The workflow will automatically:
   - Run version consistency checks
   - Run tests
   - Build the package
   - Publish to PyPI

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
