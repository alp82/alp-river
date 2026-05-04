#!/usr/bin/env bash
# PreToolUse(Agent) hook: auto-inject USER_CONTEXT and PROJECT_CONTEXT into subagents.
#
# USER_CONTEXT: MEMORY.md + every linked markdown file for the current project.
# PROJECT_CONTEXT: docs/INTENT.md, docs/STACK.md, docs/GLOSSARY.md (full bodies)
#                  plus a summary list of docs/adr/*.md, gated per-agent by READ_MAP.
#
# The two axes are independent:
#   User-aware  = agent is listed in the case statement below → receives USER_CONTEXT.
#   Project-aware = agent has an entry in READ_MAP → receives PROJECT_CONTEXT.
#
# An agent can be user-aware only, project-aware only, both, or neither:
#   User-aware Y + Project-aware Y: most agents (see case arms and READ_MAP)
#   User-aware N + Project-aware Y: health-checker, prototype-identifier,
#                                   researcher, prototyper  (user_aware=0)
#   User-aware Y + Project-aware N: visual-verifier, plan-adherence-reviewer,
#                                   setup-agent
#   User-aware N + Project-aware N: complexity-classifier, test-verifier,
#                                   accessibility-reviewer  (exit 0)
#
# Non-Agent tool calls also exit silently. Fails open on any error - missing
# files are normal.

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

user_aware=1
case "$subagent_type" in
  # User-aware: yes. Project-aware: depends on READ_MAP.
  interviewer|planner|plan-challenger|implementer|fixer|investigator|setup-agent)
    ;;
  requirements-clarifier|reuse-scanner|visual-verifier)
    ;;
  correctness-reviewer|quality-reviewer|acceptance-reviewer|plan-adherence-reviewer)
    ;;
  structure-reviewer|consistency-reviewer|reuse-reviewer)
    ;;
  security-reviewer|performance-reviewer)
    ;;
  design-consistency-reviewer|ux-reviewer)
    ;;
  # User-aware: no. Project-aware: yes (READ_MAP entries below).
  health-checker|prototype-identifier|researcher|prototyper)
    user_aware=0
    ;;
  # User-aware: no. Project-aware: no (not in READ_MAP either). Silent skip.
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

# READ_MAP: per-agent token list resolving to docs/ files.
# Tokens (lowercase) → INTENT/STACK/GLOSSARY/adr (UPPERCASE filenames, singular adr/).
# Authoritative source for project-context routing. The reads: field in agent
# frontmatter is documentation only; the hook ignores it.
declare -A READ_MAP=(
  [interviewer]="intent glossary adrs"
  [requirements-clarifier]="intent stack glossary adrs"
  [reuse-scanner]="glossary"
  [health-checker]="stack"
  [prototype-identifier]="stack"
  [researcher]="stack"
  [prototyper]="stack"
  [planner]="intent stack glossary adrs"
  [plan-challenger]="intent stack glossary adrs"
  [implementer]="stack glossary adrs"
  [correctness-reviewer]="stack glossary"
  [quality-reviewer]="intent stack glossary"
  [acceptance-reviewer]="intent glossary"
  [structure-reviewer]="glossary adrs"
  [consistency-reviewer]="glossary"
  [reuse-reviewer]="glossary"
  [security-reviewer]="stack adrs"
  [performance-reviewer]="stack"
  [ux-reviewer]="intent"
  [design-consistency-reviewer]="intent stack"
  [fixer]="stack glossary adrs"
  [investigator]="stack glossary adrs"
)

# Summarize active ADRs as a markdown bullet list. Empty string when nothing
# qualifies (no adr/ dir, no .md files, all filtered out).
summarize_adrs() {
  local adr_dir="$1"
  [ -d "$adr_dir" ] || return 0

  local out=""
  local f
  for f in "$adr_dir"/*.md; do
    [ -e "$f" ] || continue
    local base
    base=$(basename "$f")
    case "$base" in
      0000-*.md)
        continue
        ;;
    esac

    # Single awk pass extracts status, title, and a short summary. Prefers the
    # first paragraph under `## Summary`; falls back to the first paragraph after
    # the H1 title when no Summary heading is present.
    local extracted
    extracted=$(awk '
      BEGIN {
        fm = 0; fm_done = 0
        status = ""; title = ""
        pre = ""; pre_lines = 0; pre_done = 0
        post = ""; post_lines = 0; in_summary = 0
      }
      NR == 1 && /^---[[:space:]]*$/ { fm = 1; next }
      fm && !fm_done && /^---[[:space:]]*$/ { fm_done = 1; next }
      fm && !fm_done {
        if (match($0, /^[[:space:]]*status[[:space:]]*:[[:space:]]*/)) {
          status = substr($0, RSTART + RLENGTH)
          gsub(/^["'"'"']|["'"'"']$/, "", status)
          gsub(/[[:space:]]+$/, "", status)
        }
        next
      }
      title == "" && /^#[[:space:]]+/ {
        title = $0
        sub(/^#[[:space:]]+/, "", title)
        sub(/^[0-9]+[.\-][[:space:]]+/, "", title)
        sub(/^[0-9]+[[:space:]]+-[[:space:]]+/, "", title)
        gsub(/[[:space:]]+$/, "", title)
        next
      }
      title == "" { next }
      /^##[[:space:]]+[Ss]ummary[[:space:]]*$/ {
        in_summary = 1
        post = ""; post_lines = 0
        next
      }
      in_summary {
        if ($0 ~ /^#/) { in_summary = 0 }
        else if ($0 ~ /^[[:space:]]*$/) {
          if (post_lines > 0) in_summary = 0
        }
        else if (post_lines < 3) {
          if (post == "") post = $0
          else post = post " " $0
          post_lines++
        }
      }
      !pre_done && pre_lines < 3 {
        if ($0 ~ /^[[:space:]]*$/) {
          if (pre_lines > 0) pre_done = 1
        }
        else if ($0 ~ /^#/) { pre_done = 1 }
        else {
          if (pre == "") pre = $0
          else pre = pre " " $0
          pre_lines++
        }
      }
      END {
        summary = (post != "") ? post : pre
        gsub(/[[:space:]]+/, " ", summary)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", summary)
        printf "%s\t%s\t%s", status, title, summary
      }
    ' "$f")

    local status title summary
    status=$(printf '%s' "$extracted" | cut -f1)
    title=$(printf '%s' "$extracted" | cut -f2)
    summary=$(printf '%s' "$extracted" | cut -f3)

    case "$status" in
      deprecated|superseded)
        continue
        ;;
    esac

    case "$summary" in
      *_TODO:_*)
        continue
        ;;
    esac

    [ -z "$status" ] && status="unknown status"
    if [ -z "$title" ]; then
      title="${base%.md}"
    fi

    local stem="${base%.md}"
    local num="${stem%%-*}"

    out+="- ADR-${num}: ${title} [${status}]"
    [ -n "$summary" ] && out+=" - ${summary}"
    out+=" (docs/adr/${base})"$'\n'
  done

  printf '%s' "$out"
}

# Build USER_CONTEXT from MEMORY.md and its linked .md files.
# Skipped for agents that are not user-aware.
user_context=""
if [ "$user_aware" -eq 1 ] && [ -f "$memory_file" ]; then
  user_context="## USER_CONTEXT
"
  user_context+=$(cat "$memory_file")

  # Parse markdown links [Title](file.md) - only .md links, only within the memory dir.
  while IFS= read -r link_path; do
    [ -z "$link_path" ] && continue
    case "$link_path" in
      http://*|https://*|/*)
        continue
        ;;
    esac
    full_path="$memory_dir/$link_path"
    if [ -f "$full_path" ]; then
      user_context+="

---

### $link_path

"
      user_context+=$(cat "$full_path")
    fi
  done < <(grep -oE '\[[^]]*\]\([^)]+\.md\)' "$memory_file" | sed -E 's/.*\(([^)]*\.md)\).*/\1/')
fi

# Build PROJECT_CONTEXT from docs/ per the READ_MAP entry for this agent.
project_context=""
docs_dir="$project_cwd/docs"
tokens="${READ_MAP[$subagent_type]:-}"

if [ -n "$tokens" ] && [ -d "$docs_dir" ]; then
  body=""
  for token in $tokens; do
    case "$token" in
      intent)
        if [ -f "$docs_dir/INTENT.md" ]; then
          body+="### INTENT.md

"
          body+=$(cat "$docs_dir/INTENT.md")
          body+="

"
        fi
        ;;
      stack)
        if [ -f "$docs_dir/STACK.md" ]; then
          body+="### STACK.md

"
          body+=$(cat "$docs_dir/STACK.md")
          body+="

"
        fi
        ;;
      glossary)
        if [ -f "$docs_dir/GLOSSARY.md" ]; then
          body+="### GLOSSARY.md

"
          body+=$(cat "$docs_dir/GLOSSARY.md")
          body+="

"
        fi
        ;;
      adrs)
        adr_summary=$(summarize_adrs "$docs_dir/adr")
        if [ -n "$adr_summary" ]; then
          body+="### ADRs

"
          body+="$adr_summary"
          body+="
"
        fi
        ;;
    esac
  done

  if [ -n "$body" ]; then
    project_context="## PROJECT_CONTEXT
${body}"
  fi
fi

# Combine USER_CONTEXT and PROJECT_CONTEXT into one additionalContext payload.
if [ -n "$user_context" ] && [ -n "$project_context" ]; then
  assembled="${user_context}

---

${project_context}"
elif [ -n "$user_context" ]; then
  assembled="$user_context"
elif [ -n "$project_context" ]; then
  assembled="$project_context"
else
  exit 0
fi

jq -cn --arg ctx "$assembled" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $ctx}}'
