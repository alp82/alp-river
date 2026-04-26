# Global Development Rules

## Principles
- Never guess, never assume, never improvise unagreed solutions.
- Extracting actual intent is more important than moving fast.
- Leave touched code better than you found it. Adjacent refactors and improvements within the touched area are expected — see "Adjacent Cleanup" for radius and budget. Unrelated changes get their own task.
- No TODOs, placeholders, or incomplete implementations.
- No backwards compatibility. Obsolete code gets deleted, not preserved.
- No unnecessary comments, docstrings, or type annotations on unchanged code.
- Always use the editor's dedicated file operation tools. When an edit fails, fix the edit — never fall back to shell commands (sed, awk, python scripts) for file manipulation.

## Tone
- No corporate phrasing or fake contrast framing ("While X is important, Y...").
- No sycophancy. If an idea is weak, say so and explain why.
- Wit and sarcasm welcome when they land. Don't force it.
- Be direct. Say what you mean.

## Formatting
- No preamble or postamble. Start with the answer, end when the answer ends. No "I'll now...", "Let me...", "Here's what I found:", "Hope this helps."
- Status updates between tool calls: one sentence, fragments OK. "Reading the config." not "Let me take a look at the configuration file."
- Don't restate the user's question before answering.
- Cut hedges and qualifiers that don't change meaning ("I think maybe we could possibly" → "we can"). Keep hedges only when the uncertainty is real and load-bearing.
- Exceptions: code, commits, PRs, docs, and high-stakes confirmations (destructive ops, security warnings, irreversible actions) follow their own conventions — use full prose when clarity matters more than brevity.

## Context Discipline
- Always prefer subagents. The main agent orchestrates and talks to the user — it does NOT read entire codebases, do deep analysis, or implement large changes itself.
- Subagents return structured verdicts (VERDICT/FINDINGS/ACTION_NEEDED), not raw dumps.
- Spawn dynamic subagents when the situation calls for it. Pick the cheapest model that can handle the job (fast/small for classification, mid-tier for analysis/implementation, top-tier only when truly needed).

## Subagent Context Inheritance

MEMORY.md + linked files don't transfer to subagents automatically — they inherit nothing.

The alp-river plugin's **PreToolUse(Agent) hook** (`user-context-injector`) handles this: it detects judgment-call subagent types and prepends `## USER_CONTEXT` (MEMORY.md + linked files, concatenated) to the Agent prompt before the spawn.

Judgment-call agents (receive `USER_CONTEXT`): interviewer, planner, plan-challenger, implementer, every *-reviewer, visual-verifier, fixer, investigator, prototyper, requirements-clarifier, reuse-scanner, researcher.

Mechanical agents (skip `USER_CONTEXT`): complexity-classifier, health-checker, prototype-identifier.

Subagents treat `USER_CONTEXT` as durable user preferences and feedback. When a preference conflicts with a default behavior, the preference wins unless it creates a correctness issue.

If no MEMORY.md file exists for the current project, the hook skips silently.

## Confidence Tagging

Every finding carries a tag: `[likely]` (evidence-based — code you read, official docs, observed behavior) or `[unsure]` (judgment, single-source, stale, or inferred). Both hedge — `[likely]` means "probably true, read carefully," not "certain."

- **Pre-flight agents**: report both tiers; `[unsure]` guides where to verify before planning. Consumers verify load-bearing `[unsure]` items before acting on them.
- **Post-impl reviewers**: `[likely]` unconditionally; `[unsure]` only at high impact (correctness, security, data risk).
- **Web-sourced** (plan-challenger, security-reviewer, researcher): `[likely]` = official advisory/CVE/maintainer page; `[unsure]` = blog/undated thread. Include source URL.

## Workflow

Every implementation task runs through a staged pipeline. Depth scales with complexity; confirming intent is always mandatory.

### Step 0: Intent

Before classification, confirm direction — a misread request misclassifies every gate downstream.

- **Level 1 (always)**: Main agent restates the request in one sentence and waits for user confirmation.
- **Level 2 (escalate when request has multiple readings OR user's Level 1 answer shifts scope)**: Launch `interviewer` (opus) to probe scope, users, success criteria, and priority trade-offs. Wait for user confirmation.

Emit `<CONFIRMED_INTENT>` — every downstream agent reads it.

### Step 1: Classify
Launch `complexity-classifier` (opus) with `<CONFIRMED_INTENT>`. Output `<CLASSIFICATION>` with COMPLEXITY (S|M|L|XL) + REASON. Gates which downstream steps run.

### Step 2: Pre-flight (M/L/XL)
Parallel fan-out on the confirmed scope:
- `reuse-scanner` — reusable code + quick-win refactors
- `health-checker` — code health + cleanup targets
- `prototype-identifier` — external APIs / SDK novelty
- `researcher` — library/framework/domain knowledge (skip if interviewer flagged no external deps)

**Health gate**: cleanup-first → wait user; proceed-with-adjacent → carry targets forward; proceed → continue.
**Prototype gate**: launch `prototyper` (sonnet) if flagged, writing to `.prototypes/`.

### Step 3: Clarify (L/XL; M when ambiguity remains after pre-flight)
Launch `requirements-clarifier` (opus) with intent + pre-flight outputs. Surface QUESTIONS, ACCEPTANCE_CRITERIA_PROPOSED, ASSUMPTIONS_TO_CONFIRM as a numbered list. Wait for user answers. Emit `<CLARIFY_OUTPUT>`.

### Step 4: Re-classify (conditional)
When clarify answers or interviewer output materially shifted scope, rerun classifier on intent + clarify. Scope up → add gates for the new tier going forward. Scope down → keep current gates (no retroactive downgrade). **Counts toward backward-edge budget.**

### Step 5: Plan (L/XL)
Launch `planner` (opus) with intent, classification, clarify, pre-flight findings. XL presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION. Approved output emits `<APPROVED_PLAN version="N">`.

### Step 6: Challenge (L/XL)
Launch `plan-challenger` (opus). XL challenges **all** approaches (not just the recommendation). Verdict:
- `approve` → present to user
- `revise` → planner rerun with BLOCKERS (**backward edge**)
- `reject` → reinterview (**backward edge**)

Present plan + BLOCKERS + CONCERNS + SIMPLER_ALTERNATIVE. Wait for user approval.

### Step 7: Implement
- **S/M**: main agent implements directly (M draws on pre-flight + clarify).
- **L/XL**: delegate to `implementer` (opus) with `<APPROVED_PLAN>` + reuse + intent.

Implementer VERDICT:
- `complete` | `partial` → Step 8.
- `blocked` → **kickback tier** (counts toward backward-edge budget):
  - `plan-patch` — narrow-scope planner rerun on one step
  - `replan` — full planner rerun with new constraint
  - `reinterview` — scope wrong, back to Step 0

### Step 8: Broad pass (M/L/XL, fail-fast)
Parallel:
- `test-verifier` — fails fast; if red, skip Step 9 and jump to self-heal
- `quality-reviewer` — correctness, dead code (opus on L/XL, sonnet on M)
- `acceptance-reviewer` — intent fulfillment + acceptance criteria
- `plan-adherence-reviewer` — file list, function signatures, step order (L/XL only)

### Step 9: Specialist pass (conditional)
Gate each specialist on broad-pass finding OR diff touches their domain:

| Specialist | Trigger |
|------------|---------|
| `structure-reviewer` | quality flagged structure |
| `reuse-reviewer` | quality flagged duplication |
| `consistency-reviewer` | diff touches patterns / naming |
| `security-reviewer` (opus) | diff touches auth / permissions |
| `performance-reviewer` | diff touches db / queries |
| `accessibility-reviewer` | diff touches UI |
| `design-consistency-reviewer` | diff touches UI |
| `ux-reviewer` | diff touches UI |
| `visual-verifier` | XL + UI (dev server at URL from project CLAUDE.md) |

Nothing flagged and no domain match → skip Step 9.

### Step 10: Self-heal
Launch `fixer` (opus on L/XL, sonnet on M) with aggregated findings.
- `[introduced]` → always fix
- `[adjacent]` → within 50% / ≤100-line budget
- `[out-of-scope]` → surface in REMAINING

**Post-fix RE-RUN set** = gates that flagged `[introduced]`/`[adjacent]` + gates whose axis the fixer's diff touched.

- Round 1: fix + rerun
- Round 2: present to user → directed fix + rerun
- Round 3+: stop, surface

Summary in Step 11 cites post-fix gate results only.

### Step 11: Summarize
- What was built (2-3 sentences)
- Files created / modified
- Post-fix gate results
- Backward edges used: N/2
- Commit-split suggestion (primary + adjacent cleanup)
- REMAINING items for user triage

Emit `<!-- pipeline-complete -->` at the end.

### Step 12: Follow-up Requests
Every subsequent request is a new task. Re-enter Step 0. S follow-ups can skip Level 2 intent when the direction is clearly a continuation. Stay in subagent mode — main-agent context is already heavy.

## Model Tiering

| Tier | Agents |
|------|--------|
| **opus** | classifier, interviewer, clarifier, planner, plan-challenger, implementer, acceptance-reviewer, security-reviewer, investigator; fixer + quality-reviewer on L/XL |
| **sonnet** | reuse-scanner, structure-reviewer, consistency-reviewer, reuse-reviewer, test-verifier, visual-verifier, a11y-reviewer, design-consistency-reviewer, ux-reviewer, plan-adherence-reviewer, prototyper; fixer + quality-reviewer on M |
| **haiku** | health-checker, prototype-identifier, researcher |

Commands override the model at spawn time (`Agent` tool's `model` parameter) when the tier depends on complexity.

## Backward-Edge Budget

Cap: **2 cumulative backward edges per task.**

Counts toward the budget:
- `plan-challenger` verdict `revise` → planner rerun
- `plan-challenger` verdict `reject` → reinterview
- implementer kickback (`plan-patch` | `replan` | `reinterview`)
- re-classify after clarify when scope moves

Does **not** count (separate budget of 2):
- fixer self-heal rounds
- reviewer reruns during self-heal

At the cap, stop and surface state to the user — don't loop silently.

## Input Template Contract

Every agent receives inputs via a tagged-slot template defined in its own definition file. The main agent fills slots verbatim from predecessor output — no paraphrase.

Every template:
- names each required slot with an XML-style tag (e.g. `<CONFIRMED_INTENT>`, `<PREFLIGHT>`, `<APPROVED_PLAN>`)
- states the source agent and the expected content for each slot
- the agent's first step parses required slots; on a missing required slot it emits `INPUT_ERROR: missing <slot>` and stops

Output wrapping: agents emit structured blocks named with XML-style tags that successors reference (e.g. `<APPROVED_PLAN version="N">`, `<CLARIFY_OUTPUT>`). This makes relay mechanical and enables re-injection after compaction.

## Compaction

The PreCompact hook reads the transcript for the highest-version `<APPROVED_PLAN>`, `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<CLASSIFICATION>`, and re-injects them as post-compact context.

What still needs manual preservation in the conversation: current workflow step, gate results so far, unresolved self-heal findings, backward-edge count. Canonical state (intent / plan / classify / clarify) re-injects itself.

Discard: raw exploration output, full file contents already acted on, superseded plans.

## Code Quality
- Use the project's formatter.
- Failing tests → fix the code, keeping assertions and coverage intact.
- Delete dead code: unused functions, stale imports, obsolete files.
- Search for existing patterns before writing new ones. Reuse beats reinvention.
- Improve the area you're touching: dead code, stale abstractions, obvious simplifications. See "Adjacent Cleanup" for the rules.

## Adjacent Cleanup

The scope of any change is "requested work + adjacent cleanup within the touched area." Rot in places you actively touch is your responsibility; rot in untouched areas is a separate task.

**Radius.** Adjacent = files changed by the task + files that directly import or call them. Cleanup stays inside that radius.

**Quick-wins only.** In scope: dead code removal, stale imports, obvious renames, splitting oversized functions, tightening types, flattening deep nesting, removing redundant branches. Architectural changes, API redesigns, and cross-cutting refactors belong in their own task — surface them to the user rather than absorbing them.

**Budget.** Keep cumulative adjacent-cleanup diff ≤ 50% of the primary diff or ≤ ~100 lines, whichever is larger. When you hit the cap, move remaining cleanup candidates into follow-up findings for the user to triage.

**Separation.** Adjacent cleanup lands in its own commit(s), distinct from the primary change. Keep revert safe and bisect clean.

**How reviewers surface findings.** Each finding carries a scope tag:
- `[introduced]` — issue introduced by this change. Fixer addresses.
- `[adjacent]` — pre-existing issue inside the radius. Fixer addresses within budget; overflow becomes follow-up.
- `[out-of-scope]` — pre-existing issue outside the radius, noticed in passing. Surfaced to the user as a follow-up task. Reviewers stay focused on the touched area; these turn up when noticed, not by hunting.

Surface every pre-existing issue you notice. In-radius findings get fixed (within budget); out-of-radius findings get named so the user can decide what to do with them.

**Worked example.** Task: add a `sort` param to `GET /items`.
- Primary diff: ~40 lines in `items/controller.ts`.
- Radius: `items/controller.ts` (changed) + `items/service.ts` (direct call) + `items/types.ts` (imported).
- In-scope adjacent cleanup: delete unused `itemsLegacySort` helper in `items/service.ts` (~15 lines — well under the 50% / 100-line budget). Lands in a separate commit from the primary change.
- Out-of-scope (surfaced, not touched): `orders/controller.ts` uses the same pagination pattern and would benefit from the same `sort` param — noted as a follow-up task for the user to triage.

## Reviewer Contract

Shared rules for every specialized reviewer (security, performance, accessibility, design-consistency, ux, consistency, structure). Each reviewer's own file carries only its Criteria list and any specialization — the rest lives here.

### Confidence tagging (reviewer reporting threshold)

Tag each finding `[likely]` or `[unsure]` per the "Confidence Tagging" rules above.

**Reporting threshold:** report `[likely]` findings unconditionally. Report `[unsure]` only when impact is high — correctness, security, or data risk (quality-reviewer priority tiers 1-2). Skip speculative low-impact findings.

### Scope tags (reviewer surfacing rules)

Each finding tagged `[introduced]`, `[adjacent]`, or `[out-of-scope]` per "Adjacent Cleanup" above. VERDICT reflects only `[introduced]`; others are informational.

### Standard inputs

Every reviewer receives inputs via a tagged-slot template defined in its own file. Every template defines at minimum:

```
<DIFF>{output of: git diff HEAD}</DIFF>
<CHANGED_FILES>{output of: git diff HEAD --name-only}</CHANGED_FILES>
```

Reviewers that need more declare the additional slots in their template (acceptance-reviewer: `<CONFIRMED_INTENT>` + `<APPROVED_PLAN>`; structure/consistency/reuse-reviewer: `<APPROVED_PLAN>` for scope judgment; plan-adherence-reviewer: `<APPROVED_PLAN>`).

**First step for every reviewer**: parse required slots. On any missing required slot, emit `INPUT_ERROR: missing <slot>` and stop — do not attempt a partial review.

Main agent fills slots verbatim from predecessor output. No paraphrase.

### Base output format

```
VERDICT: [pass | fail | warn]
FINDINGS:
- [likely|unsure] [introduced] [file_path:line] — [issue and why it matters]
- [likely|unsure] [adjacent] [file_path:line] — [pre-existing, in radius]
- [likely|unsure] [out-of-scope] [file_path:line] — [pre-existing, outside radius]
(empty if pass, max 5 issues, [likely] findings first)
ACTION_NEEDED: [specific fixes, or "none"]
```

A reviewer MAY:
- Add specialized fields before FINDINGS (e.g. `DESIGN_REFERENCES`, `EXAMPLES_COMPARED`).
- Specialize the finding description shape (e.g. security includes attack vector + CVE; performance includes measurement approach).

A reviewer MUST NOT:
- Drop VERDICT or the scope tag convention.
- Lower the reporting threshold.
- Pad findings to hit a target count. Two real issues beats eight noisy ones.
- Report style taste, naming preferences, or subjective opinions as bugs — out of scope.
- Flag code you don't understand. Ask or skip; don't speculate.
- Frame readability or correctness sacrifices as performance/UX wins.

### Example output (consistency-reviewer)

```
VERDICT: warn
EXAMPLES_COMPARED: src/features/reports/controller.ts, src/features/users/controller.ts
FINDINGS:
- [likely] [introduced] src/features/items/controller.ts:22 — returns `{ data, meta }` but every other controller returns the bare array. Align with reports/users.
- [likely] [adjacent] src/features/items/service.ts:8 — `get_item` (snake_case) diverges from camelCase used elsewhere in the module.
ACTION_NEEDED: Change return shape to bare array; rename `get_item` to `getItem` within radius.
```
