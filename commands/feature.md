---
description: Full feature development pipeline with automatic quality gates
argument-hint: Describe the feature to build
---

# Feature Development Pipeline

Feature request: $ARGUMENTS

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents. No manual prepend.

**Input slots**: each agent defines tagged slots in its own file. Fill them verbatim from predecessor output - no paraphrase.

**Backward-edge budget**: 2 cumulative across challenger `revise`, challenger `reject`, implementer kickback, and re-classify. Track as you go.

## Step 0: Intent

**Level 1** (always): Restate the **outcome** the user wants - what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** - those belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. **Main agent stays text-only - no codebase reads, no web lookups.** Wait for user confirmation.

**Level 2** (escalate when the request has multiple plausible readings, the Level 1 answer shifted scope, OR restating would require recon): enter the **interview loop**.

- Round 1: Launch `interviewer` with `<RAW_REQUEST>`, `<L1_CONFIRMATION>`, `<PRIOR_ROUNDS>: none`.
- Each round:
  - Read `LOOKUPS_PERFORMED`, `VERDICT`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, and `DEFERRED_QUESTIONS` from the output.
  - If `VERDICT: confirmed` AND `NEW_ASPECTS_FOUND: no` → exit. Capture the final `<CONFIRMED_INTENT>` block and `EXTERNAL_DEPS_FLAG`.
  - Otherwise → if QUESTIONS is non-empty (or DEFERRED_QUESTIONS carried open items from prior rounds), apply the AGENTS.md Concise Surfacing Contract 4-cap priority queue and invoke `AskUserQuestion` with the resulting items. Do not emit a numbered prose list. Capture user answers, append `R{n}.Q{i}: ... | A: ...` per Q&A to `<PRIOR_ROUNDS>`, thread any unanswered DEFERRED_QUESTIONS into the next round's `<PRIOR_ROUNDS>`, re-launch `interviewer` with the updated `<PRIOR_ROUNDS>`.
- Cap: 5 rounds. At the cap, present the latest CONFIRMED_INTENT and remaining QUESTIONS to the user, ask them to confirm explicitly or reshape the request, and proceed only on explicit confirmation.

The interview loop is free - does NOT count toward the backward-edge budget.

## Step 1: Classify

Launch `complexity-classifier`:
- Input: `<CONFIRMED_INTENT>`

If COMPLEXITY is S or M: tell the user "this classifies as S/M - re-run under `/fix` for the lighter pipeline." Then **STOP** this command.

If COMPLEXITY is L or XL: continue.

### Gate 1: Pre-plan cost check (L/XL)

<!-- Gate 1 exclusion: Gate 1 stays as prose (binary continue/abandon decision tied to cost confirmation). AskUserQuestion would add friction for a single-keystroke choice. See AGENTS.md Concise Surfacing Contract. -->

<!-- Keep this block in sync with the matching gate block in the other command file (feature.md <-> plan.md). Edit both together. -->

After the classifier (or re-classifier) lands at L or XL **for the first time in this run**, pause before continuing to pre-flight (or, on re-classify, to Step 4).

Initialize on first fire: `<SCOPE_DOWN_COUNT> = 0`. Threaded through subsequent gate fires in this run.

**If `<SCOPE_DOWN_COUNT> < 2`**, prompt the user with one of:

- L: `This classifies as L: <REASON>. Worth it? [continue (default) / scope down / abandon] (scope-down cycles used: <SCOPE_DOWN_COUNT>/2)`
- XL: `This classifies as XL: <REASON>. Worth it? [continue / scope down / abandon] (scope-down cycles used: <SCOPE_DOWN_COUNT>/2)`

Interpret user input:
- **L**: bare Enter / empty / `y` / `yes` / `continue` -> continue.
- **XL**: any continue requires an explicit affirmative word (`y` / `yes` / `continue`); bare Enter is **not** a default - re-prompt instead.
- `scope down` / `scope-down` / `narrow` / `smaller` -> ask:
  > Ok, restating with narrower scope. What part of the work do you want to drop or postpone?

  Take the user's reply, increment `<SCOPE_DOWN_COUNT>`, feed the reply as the new `<RAW_REQUEST>` into Step 0 Level 1 restatement, and run the normal intent loop. After re-classify, this gate fires again with the updated counter.
- `abandon` / `n` / `no` / `stop` / `quit` -> stop the command; emit no `<!-- pipeline-complete -->`.

**If `<SCOPE_DOWN_COUNT> >= 2` (cap reached)**, prompt with the locked wording:

`Scope-down limit reached. Classified <tier>: <REASON>. Worth it? [continue / abandon]`

(No `scope down` option.) Interpret: continue word -> proceed. Abandon word -> stop.

Gate 1 cycles are **free** - they do not count toward the backward-edge budget.

## Step 2: Pre-flight (parallel)

Launch concurrently on the confirmed scope:
- `reuse-scanner` - reusable code + quick wins
- `health-checker` - code health + cleanup targets
- `prototype-identifier` - external APIs / SDK novelty
- `researcher` - if `EXTERNAL_DEPS_FLAG: yes`; skip otherwise

Each takes `<CONFIRMED_INTENT>` + `<TARGET_AREA>` (your best guess at the files/modules from intent).

**Health gate**: follow health-checker's RECOMMENDATION.
- `cleanup-first` → present CLEANUP_TARGETS to the user, wait for decision.
- `proceed-with-cleanup` → carry CLEANUP_TARGETS to the planner so they're folded into the plan.
- `proceed` → continue.

**Prototype gate**: if `PROTOTYPES_NEEDED: yes`, launch `prototyper` with `<PROTOTYPE_TARGETS>`. Prototypes saved to `.prototypes/` for reference.

If quick wins were found, apply them before Step 4 (they precede the plan).

## Step 3: Clarify

Enter the **clarify loop**.

- Round 1: Launch `requirements-clarifier` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>` (reuse/health/prototypes/research), `<PRIOR_ROUNDS>: none`.
- Each round:
  - Read `LOOKUPS_PERFORMED`, `CLARITY`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, `DEFERRED_QUESTIONS`, `ACCEPTANCE_CRITERIA_PROPOSED`, `ASSUMPTIONS_TO_CONFIRM`, `SCOPE_SHIFT` from the output.
  - If `CLARITY: clear` AND `NEW_ASPECTS_FOUND: no` → exit. No separate confirmation step - criteria were settled through the loop. Capture `<CLARIFY_OUTPUT>`.
  - If `CLARITY: blocked` → surface to the user; recommend reshaping. Stop the loop.
  - Otherwise → apply the AGENTS.md Concise Surfacing Contract 4-cap priority queue across QUESTIONS + [unsure] criteria + [unsure] assumptions; invoke `AskUserQuestion` with the resulting items. Surface `[likely]` ACCEPTANCE_CRITERIA_PROPOSED and `[likely]` ASSUMPTIONS_TO_CONFIRM inline as one-line confirmations above the picker (no picker needed - they're not in doubt). Capture answers, append Q&A entries per Q&A to `<PRIOR_ROUNDS>` (format: `R{n}.Q{i}: ... | A: ...`), thread DEFERRED_QUESTIONS forward, re-launch with the updated `<PRIOR_ROUNDS>`.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape; proceed only on explicit confirmation.

The clarify loop is free - does NOT count toward the backward-edge budget.

**Re-classify (backward edge)**: before exiting Step 3, if clarifier emitted `SCOPE_SHIFT: up` or `down`, OR interviewer raised scope in Step 0 that you now realize doesn't fit the original classification, rerun `complexity-classifier` with `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`.

If `SCOPE_MOVED: yes`:
- **Up to XL from L** → adopt XL gates going forward (multi-approach planner, plan-adherence reviewer already in L/XL, visual-verifier on UI).
- **Up from M to L/XL** → you're in the wrong command - tell the user "classifies as L/XL now, continuing under /feature" (you're already here, just proceed with the new tier).
- **Down** → keep current-tier gates, note downgrade, don't retract any step already executed.

**Counts as one backward edge.**

**Re-fire Gate 1**: if re-classify lands at L or XL AND Gate 1 has not yet fired in this run at L/XL (covers M->L/XL upgrade only - dormant in /feature in practice since Step 1 stops on S/M, kept for symmetry with /plan), fire the same Gate 1 block from Step 1 here, before continuing to Step 4. Use the current `<SCOPE_DOWN_COUNT>`. A scope-down here also re-enters Step 0 with the new RAW_REQUEST.

## Step 4: Plan

Launch `planner`:
- Input: `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<PREFLIGHT>`.

On XL, planner presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION.

Capture `<APPROVED_PLAN version="1">` from the output.

## Step 5: Challenge

Launch `plan-challenger`:
- Input: `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<APPROACHES>` (XL only), `<APPROVED_PLAN>`.

On XL, challenger reviews **all** approaches, then the recommendation.

Handle VERDICT:
- On VERDICT `approve`: surface BLOCKERS (one line each) and SCOPE_MISMATCH (when not "none") inline as advisory notes, then invoke `AskUserQuestion` with the challenger's `CHALLENGE_QUESTIONS` (Approve/Revise/Reshape). Map the user's selection per AGENTS.md Concise Surfacing Contract: Approve → proceed to Step 6; Revise → rerun planner with `<REPLAN_REASON>` = BLOCKERS, capture next APPROVED_PLAN version, counts as one backward edge; Reshape → reinterview from Step 0, counts as one backward edge (equivalent to challenger reject path).

If backward-edge budget is at 2 and challenger still returns `revise`/`reject`: stop, surface state to the user.

## Step 6: Implement

Launch `implementer` (opus):
- Input: `<CONFIRMED_INTENT>`, `<APPROVED_PLAN>` (current version), `<PREFLIGHT>`, `<BACKWARD_EDGES_USED>`.

Handle VERDICT:
- `complete` | `partial` → Step 7.
- `blocked` with `KICKBACK.TIER`:
  - `plan-patch` → rerun planner with `<REPLAN_REASON>` = kickback REASON, scope to the affected step. New `<APPROVED_PLAN version="N+1">`. Re-run implementer. **Counts as one backward edge.**
  - `replan` → full planner rerun with kickback REASON. **Counts as one backward edge.**
  - `reinterview` → back to Step 0. **Counts as one backward edge.** Inform user.

If backward-edge budget exhausted: stop, surface to the user.

## Step 7: Broad pass (parallel, fail-fast)

Assemble `<TOUCHED_FILES>` from the implementer's `FILES_MODIFIED` + `FILES_CREATED` output. Pass it to every reviewer below.

Launch concurrently:
- `test-verifier` - inputs `<TOUCHED_FILES>`.
- `correctness-reviewer` - inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>`. **Override model to opus** at spawn time (`model: "opus"`) since this is L/XL.
- `quality-reviewer` - inputs `<TOUCHED_FILES>`, `<APPROVED_PLAN>`. Default model is opus; no override needed.
- `acceptance-reviewer` - inputs `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<APPROVED_PLAN>`, `<TOUCHED_FILES>`.
- `plan-adherence-reviewer` - inputs `<APPROVED_PLAN>`, `<TOUCHED_FILES>`, `<IMPLEMENTER_NOTES>`.

**Fail-fast**: if `test-verifier` returns `fail`, skip Step 8 and jump to Step 9 with the test failure plus any other findings collected. Reviewing code that doesn't build wastes context.

## Step 8: Specialist pass (conditional, parallel)

Gate each specialist on broad-pass finding OR touched files matching its domain. Launch only matching specialists:

- `structure-reviewer` - broad pass flagged structure / boundaries, OR touched files include files over ~300 lines / functions over ~30 lines
- `architecture-reviewer` (opus) - touched files introduce new exports / wrappers / seams, OR broad pass flagged shallow abstraction
- `reuse-reviewer` - broad pass flagged duplication, OR touched files contain new functions similar to existing ones
- `consistency-reviewer` - touched files affect naming/error-handling/return-shape patterns
- `security-reviewer` (opus) - touched files include auth/permissions/session/input-handling
- `performance-reviewer` - touched files include database/query/hot-path code
- `accessibility-reviewer` - touched files include UI components
- `design-consistency-reviewer` - touched files include UI components
- `ux-reviewer` - touched files include UI components
- `visual-verifier` - XL and touched files include UI. Input `<TARGET>` (route/URL from project CLAUDE.md), `<CONFIRMED_INTENT>`, `<TOUCHED_FILES>`. Ask user before running on XL per the gate matrix.

Nothing flagged and no domain match → skip Step 8.

## Step 9: Self-heal

Aggregate findings from Steps 7 + 8 into `<FINDINGS>`.

Launch `fixer` - **override model to opus** at spawn time (L/XL):
- Input: `<FINDINGS>`, `<TOUCHED_FILES>`, `<APPROVED_PLAN>`, `<ROUND>`.

After the fixer runs, refresh `<TOUCHED_FILES>` to include any new files the fixer modified or created. Fixer returns `RE_RUN_SET`. Re-run exactly those gates (from Step 7 + 8) with the refreshed `<TOUCHED_FILES>`.

- **Round 1**: fix + rerun RE_RUN_SET. If still failing, go to Round 2.
- **Round 2**: present findings + fixer output to the user, ask how to proceed. Apply chosen fixes, rerun RE_RUN_SET.
- **Round 3+**: present results, stop. Do not loop silently.

Summary in Step 11 cites post-fix gate results only.

## Step 10: Capture

Aggregate every non-empty `DISCOVERIES` block from this run's upstream agents (implementer, fixer, investigator, correctness-reviewer, quality-reviewer, architecture-reviewer, structure-reviewer, consistency-reviewer, security-reviewer, performance-reviewer) into `<AGGREGATED_DISCOVERIES>`. Drop blocks where every bucket is `(none)`.

**Fold in clarifier WRITES_PROPOSED.** If `<CLARIFY_OUTPUT>` from Step 3 contained a non-empty `WRITES_PROPOSED` block (glossary terms), merge those entries into `<AGGREGATED_DISCOVERIES>` under a synthetic `requirements-clarifier` source label. They go through the same dedup + approval flow as the reviewers' discoveries.

Launch `capture-agent` (opus) with `<PHASE>: 1`, `<AGGREGATED_DISCOVERIES>`, `<APPROVALS>: n/a`.

Handle `PHASE_RESULT`:

- `complete-empty` → no novel context surfaced. Skip to Step 11.
- `complete-no-docs-dir` → surface the recommendation to the user ("docs/ not found - run /alp-river:setup if you want captures recorded next time"). Skip to Step 11.
- `proposal-ready` → present the `PROPOSAL` block to the user. Capture per-item approvals:
  - `glossary`: `accept | edit: <new text> | reject`.
  - `stack_drift` and `intent_drift`: `accept-as-drift | edit: <new text> | reject`.
  
  Re-launch `capture-agent` with `<PHASE>: 2`, the same `<AGGREGATED_DISCOVERIES>`, and `<APPROVALS>` containing the user's decisions. Capture the returned `CAPTURE_REPORT` for Step 11's summary.

Capture-agent always runs - never auto-skip. If the agent fails to spawn, treat as "no captures this round" and continue.

## Step 11: Summary

Report:
- What was built (2-3 sentences)
- Files created / modified
- Post-fix gate results (broad pass + specialists)
- Captures recorded (glossary terms, drift items appended - or "none")
- Backward edges used: N/2
- REMAINING items for user triage (anything in fixer's REMAINING)

End with the literal line `<!-- pipeline-complete -->` (HTML comment, invisible to the user). The UserPromptSubmit hook detects it and nudges classification on the next prompt.
