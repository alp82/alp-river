# Changelog

All notable changes to alp-river. Versions match `.claude-plugin/plugin.json`.

## 0.1.4 - 2026-05-02

**Clarification loops.** Intent and clarification iterate until you're satisfied. Single-pass Q&A misses the follow-up ambiguity that surfaces from your earlier answers - now each stage keeps going until nothing new comes up. Cap 5 rounds, free of the rework budget.

**Research before asking.** The agents look at the codebase and web first. If your question can be answered by reading a file or looking up a doc, they do that instead of asking you. Each round shows you what was checked.

**Orchestrator stays out of the codebase.** The main agent does the first restatement from text alone. Any deeper recon escalates to a subagent rather than dragging the orchestrator into the files.

## 0.1.3 - 2026-05-02

**Two-pass code review.** The post-implementation review now runs as two passes asking different questions:

- **Correctness asks: *does this work?*** - bugs, type holes, dead code, project-convention violations.
- **Quality asks: *is this the right way to do it?*** - the senior-engineer pass. Did the implementer pick the right tool at the right altitude with the right amount of code? Catches hacky shortcuts when a clean path exists (parsing CLI output when an SDK is already a dependency, hand-rolling retries when the library provides them), bloat (unnecessary abstraction layers, config knobs nothing reads, defensive branches for scenarios that can't happen), and wrong-altitude solutions (reinventing stdlib, wrapping typed libraries in stringly-typed structures).

Each reviewer stops sandbagging the other. Correctness no longer hides real bugs behind "this could be cleaner" notes; quality no longer waters down its judgment by chasing typos.

## 0.1.2 - 2026-05-02

**Outcome over mechanics.** Intent confirmation restates the outcome you want - what is true when this ships - not the mechanics. File paths, schema fields, function names, API routes, component names: those belong in the plan, not the read-back. If the agent can't restate the goal without naming specifics, it has over-interpreted and pulls back.

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
