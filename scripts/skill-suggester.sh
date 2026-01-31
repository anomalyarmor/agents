#!/bin/bash
# Skill suggester hook for AnomalyArmor
#
# This hook runs on UserPromptSubmit to suggest relevant skills
# based on the user's input. It outputs suggestions that Claude
# can use to recommend appropriate skills.
#
# Usage: Called automatically by Claude Code plugin system

# Get user prompt from stdin or argument
PROMPT="${1:-}"
if [ -z "$PROMPT" ]; then
    read -r PROMPT
fi

# Convert to lowercase for matching
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Check for health/status keywords
if echo "$PROMPT_LOWER" | grep -qE "(health|status|ok|working|broken|issues|problems|summary)"; then
    echo "SUGGEST: /armor:status - Check overall data health"
fi

# Check for alert keywords
if echo "$PROMPT_LOWER" | grep -qE "(alert|notification|fired|triggered|yesterday|today|week)"; then
    echo "SUGGEST: /armor:alerts - View and manage alerts"
fi

# Check for connection keywords
if echo "$PROMPT_LOWER" | grep -qE "(connect|setup|add|new).*(database|warehouse|snowflake|postgres|databricks|source)"; then
    echo "SUGGEST: /armor:connect - Connect a new data source"
fi

# Check for monitoring keywords
if echo "$PROMPT_LOWER" | grep -qE "(monitor|freshness|schedule|track|watch|stale)"; then
    echo "SUGGEST: /armor:monitor - Set up monitoring"
fi

# Check for question keywords
if echo "$PROMPT_LOWER" | grep -qE "(what|where|which|how|why|tell me|explain|describe).*(table|column|data|schema)"; then
    echo "SUGGEST: /armor:ask - Ask questions about your data"
fi

# Check for analysis keywords
if echo "$PROMPT_LOWER" | grep -qE "(analyze|analyse|generate|refresh|intelligence|ai)"; then
    echo "SUGGEST: /armor:analyze - Trigger AI analysis"
fi

# Check for onboarding keywords
if echo "$PROMPT_LOWER" | grep -qE "(start|begin|getting started|onboard|setup|first time|new to)"; then
    echo "SUGGEST: /armor:start - Guided onboarding"
fi

exit 0
