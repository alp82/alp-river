---
description: Bug fix and small change pipeline with quality gates
argument-hint: Describe the bug or change
---

# Fix Pipeline

Task: $ARGUMENTS

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents.

**Input slots**: fill each agent's input template verbatim from predecessor output.

## Step 0: Intent

**Level 1** (always): Restate the **outcome** the user wants — what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** — those belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. Wait for confirmation.

**Level 2** (escalate only when the user's answer shifts scope or the request has multiple plausible readings): Launch `interviewer`. Capture `<CONFIRMED_INTENT>`.

Most fix-sized tasks stay at Level 1.

## Step 1: Classify

Launch `complexity-classifier`:
- Input: `<CONFIRMED_INTENT>`

If COMPLEXITY is L or XL: tell the user "classifies as L/XL — re-run under `/feature` for the full pipeline." **STOP** this command.

S and M continue here.

## Step 2: Pre-flight

**S tasks**:
- Launch `reuse-scanner` in parallel with formulating your implementation.

**M tasks**:
- Launch `reuse-scanner`, `health-checker`, `prototype-identifier`, `researcher` in parallel.
- Each receives `<CONFIRMED_INTENT>` + `<TARGET_AREA>`.

**Prototype gate (M)**: if `PROTOTYPES_NEEDED: yes`, tell the user "prototyping required — this is L-territory; re-run under `/feature`. Preflight findings carry over." **STOP.**

**Health gate (M)**: follow RECOMMENDATION.
- `cleanup-first` → present CLEANUP_TARGETS, wait for user decision.
- `proceed-with-cleanup` → carry CLEANUP_TARGETS into implementation.
- `proceed` → continue.

Apply reuse-scanner QUICK_WINS when they fit the radius and budget.

## Step 3: Clarify (M only, when ambiguity remains)

If the pre-flight results leave material ambiguities, launch `requirements-clarifier` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>`. Present QUESTIONS, ACCEPTANCE_CRITERIA_PROPOSED, ASSUMPTIONS_TO_CONFIRM. Wait for answers. Capture `<CLARIFY_OUTPUT>`.

Skip when the task is clear from pre-flight alone.

## Step 4: Re-classify (M, conditional)

If clarifier returned `SCOPE_SHIFT: up`, rerun `complexity-classifier` with `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`.

If `SCOPE_MOVED: yes` and new COMPLEXITY is L or XL: tell the user "reclassifies as L/XL — re-run under `/feature`." **STOP.**

## Step 5: Implement

**S tasks**: main agent implements directly, informed by reuse findings.

**M tasks**: main agent implements, reading relevant files first. Leverage reuse findings. No planner or challenger on the M path.

## Step 6: Broad pass

**S tasks**: no subagent gates. The Stop hook runs the project's test suite automatically. Skip to Step 8.

**M tasks**: assemble `<TOUCHED_FILES>` from your own Edit/Write calls during Step 5. Launch concurrently (parallel, fail-fast):
- `test-verifier` — inputs `<TOUCHED_FILES>`.
- `correctness-reviewer` (sonnet default, no override for M) — inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`.
- `quality-reviewer` (opus default — judgment-heavy, runs at the same tier on M and L/XL) — inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`.
- `acceptance-reviewer` — inputs `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>` or `"none"`, `<APPROVED_PLAN>: none`, `<TOUCHED_FILES>`.

If `test-verifier` fails, jump to Step 7 with the test failure plus any other findings. Skip Step 7's specialist pass.

## Step 7: Specialist pass (M, conditional)

Gate each specialist on broad-pass finding OR touched files matching its domain. M tasks rarely trigger many — most are small enough that the broad pass is enough.

- `security-reviewer` — auth/permissions/session/input-handling code
- `performance-reviewer` — db/query/hot-path code
- UI specialists (`accessibility-reviewer`, `design-consistency-reviewer`, `ux-reviewer`) — UI files

Visual-verifier stays out of the M pipeline.

## Step 8: Self-heal

**S tasks**: the Stop hook handles test failure retries (1 retry per session).

**M tasks**: aggregate findings. Launch `fixer` (sonnet default):
- Input: `<FINDINGS>`, `<TOUCHED_FILES>`, `<APPROVED_PLAN>: none`, `<ROUND>`.

After the fixer runs, refresh `<TOUCHED_FILES>` to include any new files the fixer touched. Use the returned `RE_RUN_SET` to re-fire exactly those gates with the refreshed `<TOUCHED_FILES>`.

- Round 1: fix + rerun.
- Round 2: present to user, apply directed fixes, rerun.
- Round 3+: stop, surface.

Summary cites post-fix gate results.

## Step 9: Summary

Brief report:
- What was fixed (1-2 sentences)
- Files changed
- Post-fix gate results
- REMAINING items for user triage (anything in fixer's REMAINING)

End with the literal line `<!-- pipeline-complete -->`.
