---
description: Design-only workflow — classify, pre-flight, clarify, plan, challenge. Each stage driven by a specialist agent.
argument-hint: Describe the change to plan
---

# Planning Pipeline

Task: $ARGUMENTS

Design only. STOPS at an approved plan. Applying it is a separate step via `/feature` (L/XL) or `/fix` (S/M).

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents.

**Input slots**: fill each agent's template verbatim.

## Step 0: Intent

**Level 1** (always): Restate the **outcome** the user wants — what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** — those belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. **Main agent stays text-only — no codebase reads, no web lookups.** Wait for confirmation.

**Level 2** (escalate when request has multiple readings, Level 1 answer shifts scope, OR restating would require recon): enter the **interview loop**.

- Round 1: Launch `interviewer` with `<RAW_REQUEST>`, `<L1_CONFIRMATION>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `VERDICT`, `NEW_ASPECTS_FOUND`, `QUESTIONS`. Exit when `confirmed` AND `NEW_ASPECTS_FOUND: no`; capture `<CONFIRMED_INTENT>` and `EXTERNAL_DEPS_FLAG`. Otherwise present QUESTIONS, capture answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

The interview loop is free — does NOT count toward the backward-edge budget.

## Step 1: Classify

Launch `complexity-classifier` with `<CONFIRMED_INTENT>`.

- **S**: Ask the user "this is a one-liner — do you want a lightweight approach sketch, or should we jump to `/fix`?" If they want a sketch, produce 2-3 sentences + files to touch and **STOP**. Otherwise tell them "re-run under `/fix`" and **STOP**.
- **M/L/XL**: continue.

## Step 2: Pre-flight (parallel)

Launch concurrently:
- `reuse-scanner` — reusable code + quick wins
- `health-checker` — code health + cleanup targets
- `prototype-identifier` — external APIs / SDK novelty
- `researcher` — if `EXTERNAL_DEPS_FLAG: yes` from the interviewer, else skip

Each takes `<CONFIRMED_INTENT>` + `<TARGET_AREA>`.

**Health gate**: follow RECOMMENDATION (cleanup-first waits on user; proceed-with-cleanup carries targets forward; proceed continues).

**Prototype gate**: launch `prototyper` if flagged. Prototypes saved to `.prototypes/`.

## Step 3: Clarify

Enter the **clarify loop**.

- Round 1: Launch `requirements-clarifier` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `CLARITY`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, `ACCEPTANCE_CRITERIA_PROPOSED`, `ASSUMPTIONS_TO_CONFIRM`, `SCOPE_SHIFT`. Exit when `clear` AND `NEW_ASPECTS_FOUND: no`; confirm acceptance criteria with the user, then capture `<CLARIFY_OUTPUT>`. On `blocked`, surface to the user. Otherwise present the items, wait for answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

The clarify loop is free — does NOT count toward the backward-edge budget.

## Step 4: Re-classify (conditional)

If clarifier returned `SCOPE_SHIFT: up` or `down`, rerun `complexity-classifier` with `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`.

On `SCOPE_MOVED: yes`: note the new tier; the user will route to `/feature` or `/fix` accordingly in Step 6.

## Step 5: Plan

Launch `planner` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<PREFLIGHT>`.

XL presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION. Capture `<APPROVED_PLAN version="1">`.

## Step 6: Challenge (L/XL only)

Launch `plan-challenger` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<APPROACHES>` (XL only), `<APPROVED_PLAN>`.

XL challenges all approaches; L challenges the single plan.

Handle VERDICT:
- `approve` → present.
- `revise` → rerun planner with `<REPLAN_REASON>` = BLOCKERS. New `<APPROVED_PLAN version="2">`.
- `reject` → tell the user the plan is fundamentally wrong; surface the challenger output and stop.

## Step 7: Present and Stop

Show the full plan with challenger BLOCKERS/CONCERNS + SIMPLER_ALTERNATIVE appended. XL includes all approaches + recommendation.

Suggest the next step:
- L/XL → "Approve the plan? Then run `/feature` with this plan as input."
- M → "Approve the plan? Then run `/fix` with this plan as input."

Do NOT implement inside this command.

End with the literal line `<!-- pipeline-complete -->`.
