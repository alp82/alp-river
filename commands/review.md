---
description: Review specified files for quality, bugs, duplication, and dead code
argument-hint: Space-separated file paths to review
---

# Code Review

Files to review: $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user which files to review and stop.

## Process

**Memory**: Apply AGENTS.md "Subagent Context Inheritance" to the `quality-reviewer` call below.

Launch the `quality-reviewer` agent with `<TOUCHED_FILES>` set to the file paths above and `<APPROVED_PLAN>: none`. It checks bugs, duplication, dead code, and convention adherence in a single pass.

## Report

Present the quality-reviewer's output verbatim — the full `VERDICT`, `FINDINGS`, `ACTION_NEEDED`, and `OBSOLETE_CODE` block. Do not reformat or summarize the findings themselves.

Then append:

1. **Bottom line** — one sentence on the change's quality.
2. **Next command** —
   - `VERDICT: pass` → done.
   - `VERDICT: warn` → name the one or two issues worth addressing.
   - `VERDICT: fail` → suggest `/fix`, point at `ACTION_NEEDED`.
