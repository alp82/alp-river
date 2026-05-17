# Changelog

All notable changes to alp-river. Versions match `.claude-plugin/plugin.json`.

## 0.2.6 - 2026-05-17

Two changes that pull more decisions onto the page where they're easier to make:

- **Every task confirms intent first, even one-line follow-ups.** The "this is small, I'll just do it" path is gone. After any /feature or /fix pipeline, the next request - no matter how trivial - pauses for a one-sentence restate and waits for you to react. Type `yes` to roll. Type anything else (your own words, additions, corrections) and that reply becomes the new input for the interviewer, who digs deeper. Stops the misclassification cascade that happens when a tiny ask gets read as a different small ask.
- **UI design choices get an interactive picker, not a text debate.** When the clarifier sees that a task has visual or interaction choices with multiple legitimate shapes - layout, spacing, accent, density, motion, you name it - a new design-explorer agent takes over. It confirms which knobs to expose, decides whether to host the picker in a sandbox prototype or in the real page (behind a dev gate), and writes an interactive page where you flip between approaches live. Hit Copy spec on the combination you want, paste it back into chat, and the planner builds to that exact spec. Real-page hosts come with a cleanup contract so the picker artifacts never ship.

## 0.2.5 - 2026-05-16

Three changes that all push the pipeline toward "prove it, don't promise it":

- **Validation per acceptance criterion.** The planner now attaches a validation type to every acceptance criterion in the plan - `test`, `manual`, or `observable`. The acceptance reviewer enforces it: a criterion with the right code but missing its declared test (or observable, or manual flag for the user) is no longer "met". Default is `test` when in doubt; `manual` becomes a deliberate choice rather than a quiet escape hatch.
- **Visual reviewer becomes opt-in.** Auto-spawn is gone. When UI is touched, you get a single inline offer at the specialist pass - default yes on XL, default no on M/L. Stops playwright runs from firing on UI tweaks you already eyeballed; keeps the reviewer one keystroke away when you actually want it.
- **Two prototypes on high novelty.** The prototype identifier now grades each target's novelty (low/med/high). On high - when the *shape* of the solution is genuinely uncertain (streaming vs batch, push vs poll, embed vs call) - the prototyper builds two differently-shaped tracer bullets side-by-side instead of one, and reports an evidence-based comparison. Low/med novelty still get one prototype.

## 0.2.4 - 2026-05-15

The classifier now grades tasks S/M/L/XL/**XXL**. XXL means the work spans more than fits cleanly into one task - the classifier suggests how to split it, and `/feature` and `/plan` pause before any other work to ask: pick one slice and run with that, treat as XL anyway (explicit acknowledgment required, no bare-Enter default), or drop it. `/fix` hands off to `/feature` with the suggested decomposition surfaced for reference. The "treat as XL" path counts as cost confirmation, so Gate 1 doesn't fire a second time.

## 0.2.3 - 2026-05-13

Intent, clarify, and plan-critique rounds in `/feature`, `/fix`, and `/plan` now ask via a picker instead of dumping prose inline. Each option's description tells you what picking it does; the agent's recon stays in the transcript.

## 0.2.2 - 2026-05-11

Before big jobs start, `/feature` and `/plan` now pause to ask if the work is worth doing. Three answers: keep going, narrow the scope, or drop it. The plan critic also speaks up when a plan reaches farther than the goal actually needs, with a one-line "drop X to land Y" hint.

## 0.2.1 - 2026-05-10

New architecture-reviewer flags shallow wrappers, single-call modules, premature seams, and leaky interfaces via the deletion test. Quality-reviewer narrows to tool / altitude / elegance; structure-reviewer narrows to size / nesting / layer crossings - one clear owner per finding.

## 0.2.0 - 2026-05-08

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
