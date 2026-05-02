# Changelog

All notable changes to alp-river. Versions match `.claude-plugin/plugin.json`.

## 0.1.4 - 2026-05-02

Intent and clarification stages now keep iterating until you're satisfied - single-pass questioning was missing follow-up ambiguity that surfaced from your earlier answers. Each stage loops until nothing new comes up, capped at 5 rounds. Looping is free; it doesn't burn the rework budget.

The agents asking the questions now research the codebase and the web first. If your question can be answered by reading a file or looking up a doc, they do that instead of asking you. Each round shows you what was checked, so you can tell whether they actually looked.

The main agent stays text-only at the first restatement. Any deeper recon escalates to the interviewer subagent rather than dragging the orchestrator into the codebase.

## 0.1.3 - 2026-05-02

Split the post-implementation review into two passes that ask different questions:

- **Correctness review** - *does this work?* Bugs, type holes, dead code, project-convention violations.
- **Quality review** - *is this the right way to do it?* The senior-engineer code-review pass: did the implementer pick the right tool at the right altitude with the right amount of code? Catches hacky shortcuts when a clean path exists (parsing CLI output when an SDK is already a dependency, hand-rolling retries when the library provides them), bloat (unnecessary abstraction layers, config knobs nothing reads, defensive branches for scenarios that can't happen), and wrong-altitude solutions (reinventing stdlib, wrapping typed libraries in stringly-typed structures).

Splitting them stops findings from bleeding across concerns: the correctness reviewer no longer sandbags real bugs behind "this could be cleaner" notes, and the quality reviewer no longer waters down its judgment by chasing typos.

## 0.1.2 - 2026-05-02

Intent confirmation now restates the **outcome** you want - what is true when this ships - and is forbidden from naming files, schema fields, function names, API routes, or component names. Those are implementation details that belong in the plan, not the read-back. If the agent can't restate the goal without naming specifics, it has over-interpreted and pulls back.

## 0.1.1 - 2026-05-01

- Reviewers operate on the set of touched files directly, instead of receiving a pre-computed diff. Cleaner inputs, simpler invocation.
- Review scope tightened: adjacent-cleanup is its own task and no longer leaks into reviewer findings.
- Health checker and fixer logic simplified.
- Local-development workspace config added.

## 0.1.0 - 2026-04-26

Initial release.

- Multi-stage pipeline scaled by automatic complexity classification (S / M / L / XL).
- 27 subagents covering intent, classification, pre-flight, planning, implementation, broad review, specialist review, and self-heal.
- 6 slash commands: `/feature`, `/fix`, `/plan`, `/investigate`, `/review`, `/verify`.
- 8 quality hooks including session-start doctrine injection, pre-compact canonical-state re-injection, and per-agent context injection for judgment-call subagents.
