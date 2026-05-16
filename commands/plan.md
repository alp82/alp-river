---
description: Design-only workflow - classify, pre-flight, clarify, plan, challenge. Each stage driven by a specialist agent.
argument-hint: Describe the change to plan
---

# Planning Pipeline

Task: $ARGUMENTS

Design only. STOPS at an approved plan. Applying it is a separate step via `/feature` (L/XL) or `/fix` (S/M).

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook for judgment-call agents.

**Input slots**: fill each agent's template verbatim.

## Step 0: Intent

**Level 1** (always): Restate the **outcome** the user wants - what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** - those belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. **Main agent stays text-only - no codebase reads, no web lookups.** Wait for confirmation.

**Level 2** (escalate when request has multiple readings, Level 1 answer shifts scope, OR restating would require recon): enter the **interview loop**.

- Round 1: Launch `interviewer` with `<RAW_REQUEST>`, `<L1_CONFIRMATION>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `LOOKUPS_PERFORMED`, `VERDICT`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, `DEFERRED_QUESTIONS`. Exit when `confirmed` AND `NEW_ASPECTS_FOUND: no`; capture `<CONFIRMED_INTENT>` and `EXTERNAL_DEPS_FLAG`. Otherwise, if QUESTIONS is non-empty (or DEFERRED_QUESTIONS carried open items from prior rounds), apply the AGENTS.md Concise Surfacing Contract 4-cap priority queue and invoke `AskUserQuestion` with the resulting items. Do not emit a numbered prose list. Capture answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), thread any unanswered DEFERRED_QUESTIONS into the next round's `<PRIOR_ROUNDS>`, re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

The interview loop is free - does NOT count toward the backward-edge budget.

## Step 1: Classify

Launch `complexity-classifier` with `<CONFIRMED_INTENT>`.

- **S**: Ask the user "this is a one-liner - do you want a lightweight approach sketch, or should we jump to `/fix`?" If they want a sketch, produce 2-3 sentences + files to touch and **STOP**. Otherwise tell them "re-run under `/fix`" and **STOP**.
- **M**: continue without Gate 1.
- **L/XL**: continue. **Insert canonical Gate 1 block immediately below.**

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

**/plan-specific note** (outside the canonical block): on scope-down in /plan, the new RAW_REQUEST re-enters Step 0; classifier reruns; if the new classification is S, hand off ("re-run under /fix"); if M, gate does not fire; if L/XL, gate fires again.

## Step 2: Pre-flight (parallel)

Launch concurrently:
- `reuse-scanner` - reusable code + quick wins
- `health-checker` - code health + cleanup targets
- `prototype-identifier` - external APIs / SDK novelty
- `researcher` - if `EXTERNAL_DEPS_FLAG: yes` from the interviewer, else skip

Each takes `<CONFIRMED_INTENT>` + `<TARGET_AREA>`.

**Health gate**: follow RECOMMENDATION (cleanup-first waits on user; proceed-with-cleanup carries targets forward; proceed continues).

**Prototype gate**: launch `prototyper` if flagged. Prototypes saved to `.prototypes/`.

## Step 3: Clarify

Enter the **clarify loop**.

- Round 1: Launch `requirements-clarifier` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<PREFLIGHT>`, `<PRIOR_ROUNDS>: none`.
- Each round, read `LOOKUPS_PERFORMED`, `CLARITY`, `NEW_ASPECTS_FOUND`, `QUESTIONS`, `DEFERRED_QUESTIONS`, `ACCEPTANCE_CRITERIA_PROPOSED`, `ASSUMPTIONS_TO_CONFIRM`, `SCOPE_SHIFT`, `WRITES_PROPOSED`. Exit when `clear` AND `NEW_ASPECTS_FOUND: no`; no separate confirmation step - criteria were settled through the loop. Capture `<CLARIFY_OUTPUT>`. On `blocked`, surface to the user. Otherwise, apply the AGENTS.md Concise Surfacing Contract 4-cap priority queue across QUESTIONS + [unsure] criteria + [unsure] assumptions; invoke `AskUserQuestion` with the resulting items. Surface `[likely]` ACCEPTANCE_CRITERIA_PROPOSED and `[likely]` ASSUMPTIONS_TO_CONFIRM inline as one-line confirmations above the picker. Capture answers, append one-line entries to `<PRIOR_ROUNDS>` (`R{n}.Q{i}: ... | A: ...`), thread DEFERRED_QUESTIONS forward, re-launch.
- Cap: 5 rounds. At the cap, present the latest state and ask the user to confirm explicitly or reshape.

The clarify loop is free - does NOT count toward the backward-edge budget.

**On exit, surface `WRITES_PROPOSED` as info only.** If the final clarifier output contained a non-empty `WRITES_PROPOSED` block (glossary terms), present it to the user under a heading like *"The clarifier flagged these for capture - they'll be picked up if you implement under /alp-river:feature or /alp-river:fix:"* and list each item. Do NOT write any docs from this command. `/alp-river:plan` produces designs only.

**Re-classify (backward edge)**: before exiting Step 3, if clarifier returned `SCOPE_SHIFT: up` or `down`, rerun `complexity-classifier` with `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<PRIOR_CLASSIFICATION>`. On `SCOPE_MOVED: yes`, note the new tier; the user will route to `/feature` or `/fix` when implementing. Counts as one backward edge if it fires.

**Re-fire Gate 1**: if re-classify lands at L or XL AND Gate 1 has not yet fired in this run at L/XL (covers M->L/XL upgrade), fire the same Gate 1 block from Step 1 here, before continuing to Step 4. Use the current `<SCOPE_DOWN_COUNT>`.

## Step 4: Plan

Launch `planner` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<PREFLIGHT>`.

XL presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION. Capture `<APPROVED_PLAN version="1">`.

## Step 5: Challenge (L/XL only)

Launch `plan-challenger` with `<CONFIRMED_INTENT>`, `<CLASSIFICATION>`, `<CLARIFY_OUTPUT>`, `<APPROACHES>` (XL only), `<APPROVED_PLAN>`.

XL challenges all approaches; L challenges the single plan.

Handle VERDICT:
- On VERDICT `approve`: surface BLOCKERS (one line each) and SCOPE_MISMATCH (when not "none") inline as advisory notes, then invoke `AskUserQuestion` with the challenger's `CHALLENGE_QUESTIONS` (Approve/Revise/Reshape). Map the user's selection per AGENTS.md Concise Surfacing Contract: Approve → proceed to Step 6 (final readback); Revise → rerun planner with `<REPLAN_REASON>` = BLOCKERS, capture next APPROVED_PLAN version, counts as one backward edge; Reshape → stop the command with a recommendation to reinterview (equivalent to challenger reject path), counts as one backward edge.

## Step 6: Present and Stop

Show the full plan with challenger BLOCKERS/CONCERNS + SIMPLER_ALTERNATIVE + SCOPE_MISMATCH (when not "none") appended. SCOPE_MISMATCH is shown as advisory; user decides whether to act on it before running /feature or /fix. XL includes all approaches + recommendation.

Suggest the next step:
- L/XL → "Approve the plan? Then run `/feature` with this plan as input."
- M → "Approve the plan? Then run `/fix` with this plan as input."

Do NOT implement inside this command.

End with the literal line `<!-- pipeline-complete -->`.
