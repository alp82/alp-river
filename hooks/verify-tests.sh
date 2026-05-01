#!/usr/bin/env bash
# Stop hook: verify tests pass before allowing Claude to finish.
# Activates whenever the project has a detectable test command.
# Max 1 retry per session to prevent infinite loops.

set -euo pipefail

# Read hook payload from stdin (Claude Code passes JSON with session_id, transcript_path, cwd)
input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id // empty' 2>/dev/null)
cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)

# Anchor in the working directory (cwd from hook payload, fall back to $PWD)
project_root="${cwd:-$PWD}"
cd "$project_root" || exit 0

# Retry tracking: session-keyed marker so "max 1 retry" actually survives across hook invocations
# in the same Claude session (the previous $PPID approach changed every invocation).
if [ -n "$session_id" ]; then
  session_marker="/tmp/.claude-test-verify-${session_id}"
else
  # Fallback when session_id is unavailable — degrades to per-invocation (no retry limit guarantee)
  session_marker="/tmp/.claude-test-verify-fallback-$$"
fi

if [ -f "$session_marker" ]; then
  retry_count=$(cat "$session_marker")
  if [ "$retry_count" -ge 1 ]; then
    # Already retried once — let Claude finish, the quality-reviewer will catch it
    exit 0
  fi
fi

# Detect test command
test_cmd=""
if [ -f "package.json" ] && grep -q '"test"' package.json 2>/dev/null; then
  # Check it's not the default "echo Error" npm test
  test_script=$(jq -r '.scripts.test // empty' package.json 2>/dev/null)
  if [ -n "$test_script" ] && ! echo "$test_script" | grep -q "echo.*Error"; then
    test_cmd="npm test -- --reporter=dot 2>&1"
  fi
elif [ -f "pyproject.toml" ] && (grep -q 'pytest' pyproject.toml 2>/dev/null || [ -d "tests" ]); then
  if command -v uv &>/dev/null; then
    test_cmd="uv run pytest --tb=short -q 2>&1"
  elif command -v pytest &>/dev/null; then
    test_cmd="pytest --tb=short -q 2>&1"
  fi
elif [ -f "Cargo.toml" ]; then
  test_cmd="cargo test 2>&1"
elif [ -f "go.mod" ]; then
  test_cmd="go test ./... 2>&1"
fi

# No test command found — don't block
if [ -z "$test_cmd" ]; then
  exit 0
fi

# Run tests with timeout
result=$(timeout 120 bash -c "$test_cmd" 2>&1) || true
exit_code=${PIPESTATUS[0]:-$?}

if [ "$exit_code" -ne 0 ]; then
  # Track retry
  current=$(($(cat "$session_marker" 2>/dev/null || echo 0) + 1))
  echo "$current" > "$session_marker"

  # Truncate output to last 30 lines to keep context clean
  tail_output=$(echo "$result" | tail -30)

  cat <<EOF
{"decision": "block", "reason": "Tests are failing. Fix them before completing.\n\n\`\`\`\n${tail_output}\n\`\`\`"}
EOF
  exit 0
fi

# Tests passed — clean up
rm -f "$session_marker"
exit 0
