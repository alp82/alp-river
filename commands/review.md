---
description: Review current changes for quality, bugs, duplication, and dead code
---

# Code Review

Review the current uncommitted changes (or staged changes if specified).

## Context
- Current diff: !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Changed files: !`git diff HEAD --name-only`

## Process

**Memory**: Apply AGENTS.md "Subagent Context Inheritance" to the `quality-reviewer` call below.

Launch the `quality-reviewer` agent with the diff and changed files above. It checks bugs, duplication, dead code, and convention adherence in a single pass.

## Report

Present the quality-reviewer's output verbatim — the full `VERDICT`, `FINDINGS`, `ACTION_NEEDED`, and `OBSOLETE_CODE` block. Do not reformat or summarize the findings themselves.

Then append:

1. **Bottom line** — one sentence on whether the change is safe to commit.
2. **Next command** —
   - `VERDICT: pass` → state the change is safe to commit; leave the commit decision and any git operations to the user.
   - `VERDICT: warn` → name the one or two issues worth addressing; user's call.
   - `VERDICT: fail` → suggest `/fix`, point at `ACTION_NEEDED`.
