#!/usr/bin/env bash
# SessionStart hook: injects alp-river's AGENTS.md into the session as foundational context.
# The plugin lives wherever Claude Code mounts it; ${CLAUDE_PLUGIN_ROOT} resolves to that path.

set -euo pipefail

doctrine_file="${CLAUDE_PLUGIN_ROOT}/AGENTS.md"

if [[ ! -f "$doctrine_file" ]]; then
  exit 0
fi

doctrine=$(cat "$doctrine_file")

jq -n --arg ctx "$doctrine" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'
