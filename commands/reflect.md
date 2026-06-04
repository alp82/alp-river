---
description: Reflect on the current session to surface workflow friction worth tuning
argument-hint: (optional) area to focus on, e.g. "the clarify loop" or "the last fix"
---

# Reflect

Focus hint: $ARGUMENTS

Look back at the current session and surface only **big wins and big fails** worth acting on. Goal: signal that would change how alp-river is built, not a comprehensive audit.

**In-chat only.** No file writes, no memory writes, no subagent spawns. The main agent does this directly.

## Severity bar

Flag an item only if at least one holds:

- Recurring or systemic pattern, not a one-off blip.
- Real cost (tokens, wall-clock, user rounds) that would noticeably improve if fixed.
- Quality miss with downstream impact - slipped past reviewers, drove a wrong fix, misled the user.
- Workflow gap this session exposed - a step that should have fired and didn't, a spec that contradicts itself.

Routine variation, small papercuts, and "this could be slightly cleaner" do not clear the bar.

Output the items that clear the bar as plain bullets - one per item, concrete, naming the file, step, or agent. No headings, no template. If nothing clears the bar, say "Nothing clears the bar." and stop.
