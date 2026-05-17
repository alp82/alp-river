#!/usr/bin/env bash
# UserPromptSubmit hook: nudge Claude to re-classify follow-up requests
# after a /feature or /fix pipeline has just completed in the conversation.
#
# Trigger: Claude's pipeline commands write `<!-- pipeline-complete -->` at
# the end of their Step 6 summary. This hook greps for it in recent transcript
# lines. If found, it injects a classification reminder into Claude's context.

set -euo pipefail

input=$(cat)
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty' 2>/dev/null)
prompt=$(echo "$input" | jq -r '.prompt // empty' 2>/dev/null)

# Skip trivial follow-ups ("ok", "thanks", "yes") - the rule is for real requests
if [ "${#prompt}" -lt 20 ]; then
  exit 0
fi

# Need a transcript to detect pipeline completion
if [ -z "$transcript_path" ] || [ ! -f "$transcript_path" ]; then
  exit 0
fi

# Grep the tail of the transcript for the pipeline-complete marker
if tail -40 "$transcript_path" 2>/dev/null | grep -qF '<!-- pipeline-complete -->'; then
  cat <<'JSON'
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "FOLLOW-UP REMINDER: a /feature or /fix pipeline completed in this conversation. This new request is a NEW TASK - per AGENTS.md 'Follow-up Requests', classify it (S/M/L/XL) before implementing, even if it feels small. Intent confirmation is mandatory on every tier, including S: restate the outcome in 1-2 sentences and WAIT for the user. On an affirmation (y/yes/correct/proceed/looks right), continue. On any non-affirmation reply (free text, additions, corrections), treat as reshape and spawn the interviewer with that reply as the new RAW_REQUEST. Then: S -> main agent implements with stop hook. M -> /fix pipeline. L/XL -> /feature pipeline."}}
JSON
fi

exit 0
