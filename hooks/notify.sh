#!/usr/bin/env bash
# Notification hook: desktop notification when Claude needs attention.
# Works on Linux (notify-send), macOS (osascript), and falls back to terminal bell.

set -euo pipefail

input=$(cat)
title="Claude Code"
body=""

# Extract message from hook input
if echo "$input" | jq -e '.message' &>/dev/null; then
  body=$(echo "$input" | jq -r '.message // "Needs your attention"')
else
  body="Needs your attention"
fi

# Linux
if command -v notify-send &>/dev/null; then
  notify-send -u normal -t 5000 "$title" "$body" 2>/dev/null
  exit 0
fi

# macOS
if command -v osascript &>/dev/null; then
  osascript -e "display notification \"$body\" with title \"$title\"" 2>/dev/null
  exit 0
fi

# Fallback: terminal bell
printf '\a'
exit 0
