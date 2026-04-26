#!/usr/bin/env bash
# PreToolUse(Agent) hook: auto-inject USER_CONTEXT into judgment-call subagents.
#
# Reads MEMORY.md + every linked markdown file for the current project and
# emits the concatenation as additionalContext. Main agent no longer has to
# remember to prepend USER_CONTEXT to each judgment-call spawn.
#
# Skips mechanical agents (classifier, health-checker, prototype-identifier) and
# non-Agent tool calls. Fails open on any error — a missing MEMORY.md is
# normal for projects that haven't built one up.

set -euo pipefail

# Fail open if jq missing
if ! command -v jq &>/dev/null; then
  exit 0
fi

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
if [ "$tool_name" != "Agent" ]; then
  exit 0
fi

subagent_type=$(echo "$input" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null)
if [ -z "$subagent_type" ]; then
  exit 0
fi

# Judgment-call agents receive USER_CONTEXT. Mechanical agents skip.
case "$subagent_type" in
  interviewer|planner|plan-challenger|implementer|fixer|investigator|prototyper)
    ;;
  requirements-clarifier|reuse-scanner|researcher|visual-verifier)
    ;;
  quality-reviewer|acceptance-reviewer|plan-adherence-reviewer)
    ;;
  structure-reviewer|consistency-reviewer|reuse-reviewer)
    ;;
  security-reviewer|performance-reviewer|accessibility-reviewer)
    ;;
  design-consistency-reviewer|ux-reviewer)
    ;;
  complexity-classifier|health-checker|prototype-identifier)
    exit 0
    ;;
  *)
    exit 0
    ;;
esac

# Resolve project cwd → memory directory.
# Claude Code stores per-project memory under ~/.claude/projects/<encoded-cwd>/memory/
# where encoded-cwd replaces "/" with "-", so "/home/alp" becomes "-home-alp".
project_cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)
[ -z "$project_cwd" ] && project_cwd="$PWD"

encoded_cwd=$(echo "$project_cwd" | sed 's|/|-|g')
memory_dir="$HOME/.claude/projects/${encoded_cwd}/memory"
memory_file="$memory_dir/MEMORY.md"

if [ ! -f "$memory_file" ]; then
  exit 0
fi

# Assemble USER_CONTEXT: MEMORY.md followed by each linked .md file.
assembled="## USER_CONTEXT
"
assembled+=$(cat "$memory_file")

# Parse markdown links [Title](file.md) — only .md links, only within the memory dir.
while IFS= read -r link_path; do
  [ -z "$link_path" ] && continue
  # Only resolve relative paths; ignore URLs
  case "$link_path" in
    http://*|https://*|/*)
      continue
      ;;
  esac
  full_path="$memory_dir/$link_path"
  if [ -f "$full_path" ]; then
    assembled+="

---

### $link_path

"
    assembled+=$(cat "$full_path")
  fi
done < <(grep -oE '\[[^]]*\]\([^)]+\.md\)' "$memory_file" | sed -E 's/.*\(([^)]*\.md)\).*/\1/')

jq -cn --arg ctx "$assembled" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $ctx}}'
