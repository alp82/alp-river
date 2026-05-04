# Changelog

All notable changes to alp-river. Versions match `.claude-plugin/plugin.json`.

## 0.2.0 - 2026-05-04

**Subagents now know your project, not just your preferences.** Drop four files in `docs/` (intent, stack, glossary, ADRs) and every agent that needs them picks them up automatically. Planners stop suggesting libraries you've already ruled out. Reviewers stop renaming concepts you've already named. New work stops relitigating settled decisions.

Templates ship in `templates/` - copy what you want into `docs/`, fill in the gaps, ignore the rest. Anything missing just gets skipped silently.

A few small fixes folded in: accessibility-reviewer no longer receives user preferences (its job is the WCAG checklist, not what you prefer), and a couple of stale doctrine notes finally match what the code actually does.

## 0.1.5 - 2026-05-02

**`/compact` doesn't reset you anymore.** After compacting, the rules and your in-progress work (intent, classification, plan) are still there. Was supposed to work since 0.1.0 but quietly didn't.

**No more weird Step 3 → Step 5 gaps.** The old Step 4 was a rare conditional that mostly didn't fire, leaving a visible gap when you watched the pipeline run. It's now part of Step 3, so the steps go 0, 1, 2, 3, 4... in order.

## 0.1.4 - 2026-05-02

- **Intent and clarification keep asking until nothing new comes up.** They loop instead of doing a single pass. Capped at 5 rounds; doesn't count against the rework budget.
- **Agents look stuff up before bothering you.** They check the codebase and the web first, only asking what those sources don't answer. Each round shows what they checked.
- **Main agent doesn't read your code during intent confirmation.** The first restatement is from the request alone. If deeper digging is needed, a subagent does it.

## 0.1.3 - 2026-05-02

**Code review now runs in two passes:**

- **Correctness asks: *does this work?*** Bugs, type holes, dead code, convention violations.
- **Quality asks: *is this the right way?*** The senior-engineer pass. Catches hacky shortcuts when a clean path was right there (parsing CLI output when an SDK is already imported), bloat (config knobs nothing reads, defensive code for cases that can't happen), and reinvention (rolling your own when the stdlib does it).

Splitting them this way stops one from softening the other.

## 0.1.2 - 2026-05-02

The intent restatement says what should be true when the task is done, not how it'll be done. File paths, function names, and API routes belong in the plan, not in the read-back.

## 0.1.1 - 2026-05-01

- Reviewers read the changed files directly. No more pre-built diff.
- Adjacent cleanup is its own thing now, not mixed into reviewer findings.
- Health-checker and fixer cleaned up.
- Workspace config added for local dev.

## 0.1.0 - 2026-04-26

Initial release.

- A staged pipeline. Bigger tasks (L / XL) get deeper review; smaller ones (S / M) skip the gates that wouldn't add value.
- 27 subagents covering intent, classification, pre-flight, planning, implementation, review, and self-heal.
- 6 slash commands: `/feature`, `/fix`, `/plan`, `/investigate`, `/review`, `/verify`.
- 8 hooks for session start, code formatting, test verification, agent context, and notifications.
