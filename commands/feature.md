---
description: Full feature development pipeline with automatic quality gates
argument-hint: Describe the feature to build
---

# Feature Development Pipeline

Feature request: $ARGUMENTS

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents. No manual prepend.

**Input slots**: each agent defines tagged slots in its own file. Fill them verbatim from predecessor output — no paraphrase.

**Backward-edge budget**: 2 cumulative across challenger `revise`, challenger `reject`, implementer kickback, and re-classify. Track as you go.

## Step 0: Intent

**Level 1** (always): Restate the request in one sentence. Wait for user confirmation.

**Level 2** (escalate when the request has multiple plausible readings OR the Level 1 answer shifted scope): Launch `interviewer`:

- Input: `<RAW_REQUEST>`, `<L1_CONFIRMATION>`
- If `VERDICT: needs-answers` → present QUESTIONS to the user, wait for answers, re-run if needed.
- On `confirmed`, capture `<CONFIRMED_INTENT>` block for downstream use.
- Note the `EXTERNAL_DEPS_FLAG` — passed to researcher in Step 2.

## Step 1: Classify

Launch `complexity-classifier`:
- Input: `<CONFIRMED_INTENT>`

If COMPLEXITY is S or M: tell the user "this classifies as S/M — re-run under `/fix` for the lighter pipeline." Then **STOP** this command.

If COMPLEXITY is L or XL: continue.

## Step 2: Pre-flight (parallel)

Launch concurrently on the confirmed scope:
- `reuse-scanner` — reusable code + quick wins
- `health-checker` — code health + cleanup targets
- `prototype-identifier` — external APIs / SDK novelty
- `researcher` — if `EXTERNAL_DEPS_FLAG: yes`; skip otherwise

Each takes `<CONFIRMED_INTENT>` + `<TARGET_AREA>` (your best guess at the files/modules from intent).

**Health gate**: follow health-checker's RECOMMENDATION.
- `cleanup-first` → present CLEANUP_TARGETS to the user, wait for decision.
- `proceed-with-adjacent-cleanup` → carry CLEANUP_TARGETS as adjacent candidates to the planner.
- `proceed` → continue.

**Prototype gate**: if `PROTOTYPES_NEEDED: yes`, launch `prototyper` with `<PROTOTYPE_TARGETS>`. Prototypes saved to `.prototypes/` for reference.

If quick wins were found, apply them before Step 5 (they precede the plan).

## Step 3: Clarify

Launch `requirements-clarifier`:
- Input: `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>` (reuse/health/prototypes/research).

Present QUESTIONS, ACCEPTANCE_CRITERIA_PROPOSED, ASSUMPTIONS_TO_CONFIRM as a numbered list. **Wait for answers.**

On `CLARITY: clear`, still confirm the proposed acceptance criteria before proceeding. Capture `<CLARIFY_OUTPUT>`.

## Step 4: Re-classify (conditional)

If clarifier emitted `SCOPE_SHIFT: up` or `down`, OR interviewer raised scope in Step 0 that you now realize doesn't fit the original classification:

Rerun `complexity-classifier`:
- Input: `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`.

If `SCOPE_MOVED: yes`:
- **Up to XL from L** → adopt XL gates going forward (multi-approach planner, plan-adherence reviewer already in L/XL, visual-verifier on UI).
- **Up from M to L/XL** → you're in the wrong command — tell the user "classifies as L/XL now, continuing under /feature" (you're already here, just proceed with the new tier).
- **Down** → keep current-tier gates, note downgrade, don't retract any step already executed.

**Counts as one backward edge.**

## Step 5: Plan

Launch `planner`:
- Input: `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<PREFLIGHT>`.

On XL, planner presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION.

Capture `<APPROVED_PLAN version="1">` from the output.

## Step 6: Challenge

Launch `plan-challenger`:
- Input: `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<APPROACHES>` (XL only), `<APPROVED_PLAN>`.

On XL, challenger reviews **all** approaches, then the recommendation.

Handle VERDICT:
- `approve` → present plan + BLOCKERS + CONCERNS + SIMPLER_ALTERNATIVE to the user, wait for approval.
- `revise` → rerun planner with `<REPLAN_REASON>` = BLOCKERS. Capture new `<APPROVED_PLAN version="2">`. **Counts as one backward edge.**
- `reject` → reinterview (back to Step 0). **Counts as one backward edge.** Inform the user why.

If backward-edge budget is at 2 and challenger still returns `revise`/`reject`: stop, surface state to the user.

## Step 7: Implement

Launch `implementer` (opus):
- Input: `<CONFIRMED_INTENT>`, `<APPROVED_PLAN>` (current version), `<PREFLIGHT>`, `<BACKWARD_EDGES_USED>`.

Handle VERDICT:
- `complete` | `partial` → Step 8.
- `blocked` with `KICKBACK.TIER`:
  - `plan-patch` → rerun planner with `<REPLAN_REASON>` = kickback REASON, scope to the affected step. New `<APPROVED_PLAN version="N+1">`. Re-run implementer. **Counts as one backward edge.**
  - `replan` → full planner rerun with kickback REASON. **Counts as one backward edge.**
  - `reinterview` → back to Step 0. **Counts as one backward edge.** Inform user.

If backward-edge budget exhausted: stop, surface to the user.

## Step 8: Broad pass (parallel, fail-fast)

Launch concurrently:
- `test-verifier` — inputs `<DIFF>`, `<CHANGED_FILES>`.
- `quality-reviewer` — inputs `<DIFF>`, `<CHANGED_FILES>`, `<APPROVED_PLAN>`. **Override model to opus** at spawn time (`model: "opus"`) since this is L/XL.
- `acceptance-reviewer` — inputs `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<APPROVED_PLAN>`, `<DIFF>`, `<CHANGED_FILES>`.
- `plan-adherence-reviewer` — inputs `<APPROVED_PLAN>`, `<DIFF>`, `<CHANGED_FILES>`, `<IMPLEMENTER_NOTES>`.

**Fail-fast**: if `test-verifier` returns `fail`, skip Step 9 and jump to Step 10 with the test failure plus any other findings collected. Reviewing code that doesn't build wastes context.

## Step 9: Specialist pass (conditional, parallel)

Gate each specialist on broad-pass finding OR diff touching its domain. Launch only matching specialists:

- `structure-reviewer` — quality flagged structure issue, OR diff has files over ~300 lines / functions over ~30 lines
- `reuse-reviewer` — quality flagged duplication, OR diff contains new functions similar to existing ones
- `consistency-reviewer` — diff touches naming/error-handling/return-shape patterns
- `security-reviewer` (opus) — diff touches auth/permissions/session/input-handling
- `performance-reviewer` — diff touches database/query/hot-path code
- `accessibility-reviewer` — diff touches UI components
- `design-consistency-reviewer` — diff touches UI components
- `ux-reviewer` — diff touches UI components
- `visual-verifier` — XL and diff touches UI. Input `<TARGET>` (route/URL from project CLAUDE.md), `<CONFIRMED_INTENT>`, `<DIFF>`, `<CHANGED_FILES>`. Ask user before running on XL per the gate matrix.

Nothing flagged and no domain match → skip Step 9.

## Step 10: Self-heal

Aggregate findings from Steps 8 + 9 into `<FINDINGS>`.

Launch `fixer` — **override model to opus** at spawn time (L/XL):
- Input: `<FINDINGS>`, `<DIFF>` (primary), `<CHANGED_FILES>`, `<APPROVED_PLAN>`, `<ROUND>`.

Fixer returns `RE_RUN_SET`. Re-run exactly those gates (from Step 8 + 9) with the post-fix diff.

- **Round 1**: fix + rerun RE_RUN_SET. If still failing, go to Round 2.
- **Round 2**: present findings + fixer output to the user, ask how to proceed. Apply chosen fixes, rerun RE_RUN_SET.
- **Round 3+**: present results, stop. Do not loop silently.

Summary in Step 11 cites post-fix gate results only.

## Step 11: Summary

Report:
- What was built (2-3 sentences)
- Files created / modified
- Post-fix gate results (broad pass + specialists)
- Backward edges used: N/2
- Commit-split suggestion: name the primary commit message and the `chore:` adjacent-cleanup commit (leave execution to the user — never run git writes)
- REMAINING `[out-of-scope]` items for user triage

End with the literal line `<!-- pipeline-complete -->` (HTML comment, invisible to the user). The UserPromptSubmit hook detects it and nudges classification on the next prompt.
