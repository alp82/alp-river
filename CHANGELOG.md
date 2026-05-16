# Changelog

All notable changes to alp-river. Versions match `.claude-plugin/plugin.json`.

## 0.2.3 - 2026-05-17

Intent, clarify, and plan-critique rounds in `/feature`, `/fix`, and `/plan` now ask via a picker instead of dumping prose inline. Each option's description tells you what picking it does; the agent's recon stays in the transcript.

## 0.2.2 - 2026-05-16

Before big jobs start, `/feature` and `/plan` now pause to ask if the work is worth doing. Three answers: keep going, narrow the scope, or drop it. The plan critic also speaks up when a plan reaches farther than the goal actually needs, with a one-line "drop X to land Y" hint.

## 0.2.1 - 2026-05-15

New architecture-reviewer flags shallow wrappers, single-call modules, premature seams, and leaky interfaces via the deletion test. Quality-reviewer narrows to tool / altitude / elegance; structure-reviewer narrows to size / nesting / layer crossings - one clear owner per finding.

## 0.2.0 - 2026-05-10

Subagents read your project's intent, stack, glossary, and ADRs from `docs/` automatically - planners stop suggesting ruled-out libraries, reviewers stop renaming named concepts. `/alp-river:setup` bootstraps those docs interview-style; templates ship in `templates/`.

Reviewers and the implementer record novel terms and stack/intent drift during a run; at the end you pick what to keep. `/alp-river:adr` drafts a single decision record from a title + summary, rejecting duplicates of active ADRs.

Smaller: accessibility-reviewer no longer receives user preferences (WCAG only); per-agent context wiring consolidated to one hook.

## 0.1.5 - 2026-05-02

`/compact` no longer resets in-progress work - rules, intent, classification, and plan all persist (was meant to work since 0.1.0; quietly didn't). Pipeline steps also read sequentially now: the old Step 4 was a rare conditional that left a visible gap; folded into Step 3.

## 0.1.4 - 2026-05-02

- **Intent and clarification keep asking until nothing new comes up.** They loop instead of doing a single pass. Capped at 5 rounds; doesn't count against the rework budget.
- **Agents look stuff up before bothering you.** They check the codebase and the web first, only asking what those sources don't answer. Each round shows what they checked.
- **Main agent doesn't read your code during intent confirmation.** The first restatement is from the request alone. If deeper digging is needed, a subagent does it.

## 0.1.3 - 2026-05-02

Code review runs in two passes now:
- **Correctness**: bugs, type holes, dead code, convention violations.
- **Quality**: hacky shortcuts, bloat, wrong tool for the job.

Splitting them stops one from softening the other.

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
