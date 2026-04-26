---
description: Visual verification of UI changes using playwright-cli screenshots
argument-hint: Optional URL or component to verify
---

# Visual Verification

Target: $ARGUMENTS

**Memory**: Prepend `USER_CONTEXT` to `visual-verifier` per AGENTS.md §"Subagent Context Inheritance".

Launch the `visual-verifier` agent with:
- The target URL or component (from arguments, or auto-detect from recent changes)
- The current git diff to understand what changed: !`git diff HEAD --name-only`

Report the results and display any screenshots taken.
