---
description: Bug fix and small change pipeline with quality gates
argument-hint: Describe the bug or change
---

# Fix Pipeline

Task: $ARGUMENTS

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents.

**Input slots**: fill each agent's input template verbatim from predecessor output.

## Step 0: Intent

**Level 1** (always): Restate the **outcome** the user wants - what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** - those belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. **Main agent stays text-only - no codebase reads, no web lookups.** Wait for confirmation.

**Level 2** (escalate when the user's answer shifts scope, the request has multiple plausible readings, OR restating would require recon): enter the **interview loop**.

- Round 1: Launch `interviewer` with `<RAW_REQUEST>`, `<L1_CONFIRMATION>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `VERDICT`, `NEW_ASPECTS_FOUND`, `QUESTIONS`. Exit when `confirmed` AND `NEW_ASPECTS_FOUND: no`; capture `<CONFIRMED_INTENT>` and `EXTERNAL_DEPS_FLAG`. Otherwise present QUESTIONS, capture answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

The interview loop is free - does NOT count toward the backward-edge budget. Most fix-sized tasks stay at Level 1.

## Step 1: Classify

Launch `complexity-classifier`:
- Input: `<CONFIRMED_INTENT>`

If COMPLEXITY is L or XL: tell the user "classifies as L/XL - re-run under `/feature` for the full pipeline." **STOP** this command.

S and M continue here.

## Step 2: Pre-flight

**S tasks**:
- Launch `reuse-scanner` in parallel with formulating your implementation.

**M tasks**:
- Launch `reuse-scanner`, `health-checker`, `prototype-identifier`, `researcher` in parallel.
- Each receives `<CONFIRMED_INTENT>` + `<TARGET_AREA>`.

**Prototype gate (M)**: if `PROTOTYPES_NEEDED: yes`, tell the user "prototyping required - this is L-territory; re-run under `/feature`. Preflight findings carry over." **STOP.**

**Health gate (M)**: follow RECOMMENDATION.
- `cleanup-first` → present CLEANUP_TARGETS, wait for user decision.
- `proceed-with-cleanup` → carry CLEANUP_TARGETS into implementation.
- `proceed` → continue.

Apply reuse-scanner QUICK_WINS when they fit the radius and budget.

## Step 3: Clarify (M only, when ambiguity remains)

If the pre-flight results leave material ambiguities, enter the **clarify loop**.

- Round 1: Launch `requirements-clarifier` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `CLARITY`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, `ACCEPTANCE_CRITERIA_PROPOSED`, `ASSUMPTIONS_TO_CONFIRM`, `SCOPE_SHIFT`. Exit when `clear` AND `NEW_ASPECTS_FOUND: no`; capture `<CLARIFY_OUTPUT>`. On `blocked`, surface to the user. Otherwise present the items, wait for answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

Skip the loop entirely when the task is clear from pre-flight alone. The clarify loop is free - does NOT count toward the backward-edge budget.

**Re-classify (backward edge)**: before exiting Step 3, if clarifier returned `SCOPE_SHIFT: up`, rerun `complexity-classifier` with `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`. If `SCOPE_MOVED: yes` and new COMPLEXITY is L or XL, tell the user "reclassifies as L/XL - re-run under `/feature`" and **STOP**. Counts as one backward edge if it fires.

## Step 4: Implement

**S tasks**: main agent implements directly, informed by reuse findings.

**M tasks**: main agent implements, reading relevant files first. Leverage reuse findings. No planner or challenger on the M path.

## Step 5: Broad pass

**S tasks**: no subagent gates. The Stop hook runs the project's test suite automatically. Skip to Step 7.

**M tasks**: assemble `<TOUCHED_FILES>` from your own Edit/Write calls during Step 4. Launch concurrently (parallel, fail-fast):
- `test-verifier` - inputs `<TOUCHED_FILES>`.
- `correctness-reviewer` (sonnet default, no override for M) - inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`.
- `quality-reviewer` (opus default - judgment-heavy, runs at the same tier on M and L/XL) - inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`.
- `acceptance-reviewer` - inputs `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>` or `"none"`, `<APPROVED_PLAN>: none`, `<TOUCHED_FILES>`.

If `test-verifier` fails, skip the specialist pass and jump to Step 7 (self-heal) with the test failure plus any other findings.

## Step 6: Specialist pass (M, conditional)

Gate each specialist on broad-pass finding OR touched files matching its domain. M tasks rarely trigger many - most are small enough that the broad pass is enough.

- `security-reviewer` - auth/permissions/session/input-handling code
- `performance-reviewer` - db/query/hot-path code
- UI specialists (`accessibility-reviewer`, `design-consistency-reviewer`, `ux-reviewer`) - UI files

Visual-verifier stays out of the M pipeline.

## Step 7: Self-heal

**S tasks**: the Stop hook handles test failure retries (1 retry per session).

**M tasks**: aggregate findings. Launch `fixer` (sonnet default):
- Input: `<FINDINGS>`, `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`, `<ROUND>`.

After the fixer runs, refresh `<TOUCHED_FILES>` to include any new files the fixer touched. Use the returned `RE_RUN_SET` to re-fire exactly those gates with the refreshed `<TOUCHED_FILES>`.

- Round 1: fix + rerun.
- Round 2: present to user, apply directed fixes, rerun.
- Round 3+: stop, surface.

Summary cites post-fix gate results.

## Step 8: Capture

**S tasks**: skip - no upstream emitters ran.

**M tasks**: aggregate every non-empty `DISCOVERIES` block from this run's upstream agents (implementer was you, but fixer + the broad/specialist reviewers all emit) into `<AGGREGATED_DISCOVERIES>`. Drop blocks where every bucket is `(none)`.

Launch `capture-agent` (opus) with `<PHASE>: 1`, `<AGGREGATED_DISCOVERIES>`, `<APPROVALS>: n/a`.

Handle `PHASE_RESULT`:

- `complete-empty` → no novel context surfaced. Skip to Step 9.
- `complete-no-docs-dir` → surface the recommendation to the user ("docs/ not found - run /alp-river:setup if you want captures recorded next time"). Skip to Step 9.
- `proposal-ready` → present the `PROPOSAL` block to the user. Capture per-item approvals in the format `BUCKET.INDEX: accept | edit: <new text> | reject`. Re-launch `capture-agent` with `<PHASE>: 2`, the same `<AGGREGATED_DISCOVERIES>`, and `<APPROVALS>`. Capture the returned `CAPTURE_REPORT` for Step 9's summary.

Capture-agent always runs on M - never auto-skip. If the agent fails to spawn, treat as "no captures this round" and continue.

## Step 9: Summary

Brief report:
- What was fixed (1-2 sentences)
- Files changed
- Post-fix gate results
- Captures recorded (glossary terms, ADRs created, drift items appended - or "none"; M only)
- REMAINING items for user triage (anything in fixer's REMAINING)

End with the literal line `<!-- pipeline-complete -->`.
