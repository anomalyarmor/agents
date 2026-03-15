#!/usr/bin/env bash
# Validate that all skills have the required auth hook.
#
# The skill YAML format doesn't support shared/inherited hooks,
# so each SKILL.md must duplicate the auth block. This script
# ensures consistency across all skills.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$REPO_ROOT/skills"

EXPECTED_HOOK='command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"'

errors=0
checked=0

for skill_file in "$SKILLS_DIR"/*/SKILL.md; do
    skill_name="$(basename "$(dirname "$skill_file")")"
    checked=$((checked + 1))

    if ! grep -q "$EXPECTED_HOOK" "$skill_file"; then
        echo "FAIL: skills/$skill_name/SKILL.md missing auth hook"
        errors=$((errors + 1))
    fi
done

if [ "$errors" -gt 0 ]; then
    echo ""
    echo "$errors/$checked skills missing auth hook. Expected in YAML frontmatter:"
    echo "  $EXPECTED_HOOK"
    exit 1
fi

echo "OK: $checked skills all have auth hook configured"
