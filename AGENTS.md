# Global Development Rules

## Principles
- Never guess, never assume, never improvise unagreed solutions.
- Extracting actual intent is more important than moving fast.
- Research before asking. Subagents exhaust filesystem, tools, and web first; questions only surface what those sources don't already answer.
- Clarify in loops, not single passes. Intent and clarification stages re-run with prior rounds folded in until the latest exchange surfaces no new aspects. Loops within one step are free and do not count as backward edges.
- Leave touched code better than you found it. Unrelated changes get their own task.
- No TODOs, placeholders, or incomplete implementations.
- No backwards compatibility. Obsolete code gets deleted, not preserved.
- No unnecessary comments, docstrings, or type annotations on unchanged code.
- Always use the editor's dedicated file operation tools. When an edit fails, fix the edit - never fall back to shell commands (sed, awk, python scripts) for file manipulation.

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
- Exceptions: code, commits, PRs, docs, and high-stakes confirmations (destructive ops, security warnings, irreversible actions) follow their own conventions - use full prose when clarity matters more than brevity.

## Context Discipline
- Always prefer subagents. The main agent orchestrates and talks to the user - it does NOT read entire codebases, do deep analysis, or implement large changes itself.
- Subagents return structured verdicts (VERDICT/FINDINGS/ACTION_NEEDED), not raw dumps.
- Spawn dynamic subagents when the situation calls for it. Pick the cheapest model that can handle the job (fast/small for classification, mid-tier for analysis/implementation, top-tier only when truly needed).

## Subagent Context Inheritance

MEMORY.md + linked files don't transfer to subagents automatically - they inherit nothing. Neither do project-level docs.

The alp-river plugin's **PreToolUse(Agent) hook** (`user-context-injector`) handles both. It prepends up to two blocks to the Agent prompt:

- `## USER_CONTEXT` - MEMORY.md + linked files (durable user preferences and feedback).
- `## PROJECT_CONTEXT` - matching slices of the project's `docs/` folder (intent, stack, glossary, ADRs).

The two axes are independent. User-aware status does not determine project-aware status, and vice versa.

**User-aware** means the agent receives `## USER_CONTEXT`. The hook's case statement is the allowlist. When a user preference conflicts with a default behavior, the preference wins unless it creates a correctness issue.

**Project-aware** means the agent receives `## PROJECT_CONTEXT`. The hook's `READ_MAP` is the allowlist. Each entry lists which doc tokens the agent needs (`intent`, `stack`, `glossary`, `adrs`).

Per-agent assignment, grouped by workflow stage:

| Agent | User-aware | Project-aware |
|-------|:----------:|:-------------:|
| **Understand** | | |
| interviewer | Y | Y |
| complexity-classifier | N | N |
| **Prepare** | | |
| reuse-scanner | Y | Y |
| health-checker | N | Y |
| prototype-identifier | N | Y |
| researcher | N | Y |
| prototyper | N | Y |
| requirements-clarifier | Y | Y |
| **Design** | | |
| planner | Y | Y |
| plan-challenger | Y | Y |
| **Build** | | |
| implementer | Y | Y |
| **Verify** | | |
| test-verifier | N | N |
| correctness-reviewer | Y | Y |
| quality-reviewer | Y | Y |
| acceptance-reviewer | Y | Y |
| plan-adherence-reviewer | Y | N |
| structure-reviewer | Y | Y |
| consistency-reviewer | Y | Y |
| reuse-reviewer | Y | Y |
| security-reviewer | Y | Y |
| performance-reviewer | Y | Y |
| accessibility-reviewer | N | N |
| design-consistency-reviewer | Y | Y |
| ux-reviewer | Y | Y |
| visual-verifier | Y | N |
| fixer | Y | Y |
| **Cross-cutting** | | |
| investigator | Y | Y |

If no MEMORY.md exists for the current project, the hook skips the USER_CONTEXT block silently. A missing `docs/` folder omits the whole PROJECT_CONTEXT block. Per-doc silent skip: a missing token target (e.g. no `INTENT.md`) just omits that slice. No errors, no scaffolding prompts.

### Project Context docs

Project intent, stack choices, glossary, and prior architectural decisions live in your repo's `docs/` folder.

Four file types feed it. Token names are lowercase; resolved filenames are UPPERCASE to match README/CHANGELOG/LICENSE convention. ADRs live in `docs/adr/` per the standard ADR convention.

| Token | Resolves to | How it appears |
|-------|-------------|----------------|
| `intent` | `docs/INTENT.md` | full body under `### INTENT.md` |
| `stack` | `docs/STACK.md` | full body under `### STACK.md` |
| `glossary` | `docs/GLOSSARY.md` | full body under `### GLOSSARY.md` |
| `adrs` | `docs/adr/*.md` | summary list - one bullet per ADR with status, title, summary, path |

ADRs collapse to a list, not full bodies, to keep prompts lean. The hook drops ADRs with status `deprecated` or `superseded`, files matching `0000-*.md` (catches the unfilled template), and ADRs whose summary still contains a `_TODO:_` marker.

The mapping from agent to tokens lives inside the hook (`READ_MAP`) and is the authoritative source. Each agent file also carries a `reads:` field in its frontmatter as documentation for agent authors - the hook ignores it. Templates ship in the plugin's `templates/` folder; copy them into your project's `docs/` and fill in the `_TODO:_` markers.

## Confidence Tagging

Every finding carries a tag: `[likely]` (evidence-based - code you read, official docs, observed behavior) or `[unsure]` (judgment, single-source, stale, or inferred). Both hedge - `[likely]` means "probably true, read carefully," not "certain."

- **Pre-flight agents**: report both tiers; `[unsure]` guides where to verify before planning. Consumers verify load-bearing `[unsure]` items before acting on them.
- **Post-impl reviewers**: `[likely]` unconditionally; `[unsure]` only at high impact (correctness, security, data risk).
- **Web-sourced** (plan-challenger, security-reviewer, researcher): `[likely]` = official advisory/CVE/maintainer page; `[unsure]` = blog/undated thread. Include source URL.

## Workflow

Every implementation task runs through a staged pipeline. Depth scales with complexity; confirming intent is always mandatory.

### Step 0: Intent

Before classification, confirm direction - a misread request misclassifies every gate downstream.

- **Level 1 (always)**: Main agent restates the **outcome** the user wants - what needs to be true when this is done, in user-observable terms. Keep it concise; clarity wins over brevity, so use a couple of sentences, a small ASCII diagram, or a brief example if that lands the point better than prose. **No file paths, schema fields, function names, API routes, or component names** - those are implementation details that belong in the plan, not the intent. If you can't restate without naming specifics, you've over-interpreted; pull back to the goal. **Main agent stays text-only - no codebase reads, no web lookups.** Wait for user confirmation.
- **Level 2 (escalate when request has multiple readings, Level 1 answer shifts scope, OR restating would require recon)**: enter the **interview loop**. Launch `interviewer` (opus) to research the target area (filesystem + web when relevant), then probe scope, users, success criteria, and priority trade-offs. Each round, present QUESTIONS to the user, capture answers, append to `<PRIOR_ROUNDS>`, re-launch. Exit when `VERDICT: confirmed` AND `NEW_ASPECTS_FOUND: no`. Cap at 5 rounds - at the cap, present the latest direction and ask the user to confirm or reshape.

Emit `<CONFIRMED_INTENT>` - every downstream agent reads it.

### Step 1: Classify
Launch `complexity-classifier` (opus) with `<CONFIRMED_INTENT>`. Output `<CLASSIFICATION>` with COMPLEXITY (S|M|L|XL) + REASON. Gates which downstream steps run.

### Step 2: Pre-flight (M/L/XL)
Parallel fan-out on the confirmed scope:
- `reuse-scanner` - reusable code + quick-win refactors
- `health-checker` - code health + cleanup targets
- `prototype-identifier` - external APIs / SDK novelty
- `researcher` - library/framework/domain knowledge (skip if interviewer flagged no external deps)

**Health gate**: cleanup-first → wait user; proceed-with-cleanup → carry targets forward; proceed → continue.
**Prototype gate**: launch `prototyper` (sonnet) if flagged, writing to `.prototypes/`.

### Step 3: Clarify (L/XL; M when ambiguity remains after pre-flight)
Enter the **clarify loop**. Launch `requirements-clarifier` (opus) with intent + pre-flight outputs. Surface QUESTIONS, ACCEPTANCE_CRITERIA_PROPOSED, ASSUMPTIONS_TO_CONFIRM as a numbered list. Wait for user answers, append to `<PRIOR_ROUNDS>`, re-launch. Exit when `CLARITY: clear` AND `NEW_ASPECTS_FOUND: no`. Cap at 5 rounds - at the cap, present the latest state and ask the user to confirm or reshape. Emit `<CLARIFY_OUTPUT>`.

**Re-classify (backward edge)**: before exiting Step 3, if clarify answers (or earlier interviewer output) materially shifted scope, rerun `complexity-classifier` on intent + clarify. Scope up → add gates for the new tier going forward. Scope down → keep current gates (no retroactive downgrade). **Counts toward backward-edge budget.**

### Step 4: Plan (L/XL)
Launch `planner` (opus) with intent, classification, clarify, pre-flight findings. XL presents 2-3 APPROACHES with ASCII diagrams + RECOMMENDATION. Approved output emits `<APPROVED_PLAN version="N">`.

### Step 5: Challenge (L/XL)
Launch `plan-challenger` (opus). XL challenges **all** approaches (not just the recommendation). Verdict:
- `approve` → present to user
- `revise` → planner rerun with BLOCKERS (**backward edge**)
- `reject` → reinterview (**backward edge**)

Present plan + BLOCKERS + CONCERNS + SIMPLER_ALTERNATIVE. Wait for user approval.

### Step 6: Implement
- **S/M**: main agent implements directly (M draws on pre-flight + clarify).
- **L/XL**: delegate to `implementer` (opus) with `<APPROVED_PLAN>` + reuse + intent.

Implementer VERDICT:
- `complete` | `partial` → Step 7.
- `blocked` → **kickback tier** (counts toward backward-edge budget):
  - `plan-patch` - narrow-scope planner rerun on one step
  - `replan` - full planner rerun with new constraint
  - `reinterview` - scope wrong, back to Step 0

### Step 7: Broad pass (M/L/XL, fail-fast)
Parallel:
- `test-verifier` - fails fast; if red, skip Step 8 and jump to self-heal
- `correctness-reviewer` - correctness, type holes, dead code (opus on L/XL, sonnet on M)
- `quality-reviewer` - engineering judgment: hacky shortcuts, bloat, wrong tool, unelegant (opus across)
- `acceptance-reviewer` - intent fulfillment + acceptance criteria
- `plan-adherence-reviewer` - file list, function signatures, step order (L/XL only)

### Step 8: Specialist pass (conditional)
Gate each specialist on broad-pass finding OR touched files matching its domain:

| Specialist | Trigger |
|------------|---------|
| `structure-reviewer` | broad pass flagged structure / boundaries |
| `reuse-reviewer` | broad pass flagged duplication |
| `consistency-reviewer` | touched files affect patterns / naming |
| `security-reviewer` (opus) | touched files include auth / permissions |
| `performance-reviewer` | touched files include db / queries |
| `accessibility-reviewer` | touched files include UI |
| `design-consistency-reviewer` | touched files include UI |
| `ux-reviewer` | touched files include UI |
| `visual-verifier` | XL + UI (dev server at URL from project CLAUDE.md) |

Nothing flagged and no domain match → skip Step 8.

### Step 9: Self-heal
Launch `fixer` (opus on L/XL, sonnet on M) with aggregated findings. Fixer addresses every reported finding; anything that can't be fixed in scope goes into REMAINING.

**Post-fix RE-RUN set** = gates that flagged anything the fixer addressed + gates whose domain the fixer's edits touched.

- Round 1: fix + rerun
- Round 2: present to user → directed fix + rerun
- Round 3+: stop, surface

Summary in Step 10 cites post-fix gate results only.

### Step 10: Summarize
- What was built (2-3 sentences)
- Files created / modified
- Post-fix gate results
- Backward edges used: N/2
- REMAINING items for user triage

Emit `<!-- pipeline-complete -->` at the end.

### Step 11: Follow-up Requests
Every subsequent request is a new task. Re-enter Step 0. S follow-ups can skip Level 2 intent when the direction is clearly a continuation. Stay in subagent mode - main-agent context is already heavy.

## Model Tiering

| Tier | Agents |
|------|--------|
| **opus** | classifier, interviewer, clarifier, planner, plan-challenger, implementer, acceptance-reviewer, security-reviewer, investigator, quality-reviewer; fixer + correctness-reviewer on L/XL |
| **sonnet** | reuse-scanner, structure-reviewer, consistency-reviewer, reuse-reviewer, test-verifier, visual-verifier, a11y-reviewer, design-consistency-reviewer, ux-reviewer, plan-adherence-reviewer, prototyper; fixer + correctness-reviewer on M |
| **haiku** | health-checker, prototype-identifier, researcher |

Commands override the model at spawn time (`Agent` tool's `model` parameter) when the tier depends on complexity.

## Clarification Loops

Step 0 Level 2 (interviewer) and Step 3 (clarifier) run as loops, not single passes. Depth scales with the unknowns still lurking - keep going until the user is satisfied and no new aspects emerge.

**Exit criteria** - exit when ALL hold:
1. Agent's VERDICT is `confirmed` (interviewer) or `clear` (clarifier).
2. Agent's `NEW_ASPECTS_FOUND: no`.
3. User has no further additions.

**Cap**: 5 rounds per stage. At the cap, present the latest state and ask the user to confirm explicitly or reshape the request. Do not loop silently.

**Round inputs**: re-invocations carry `<PRIOR_ROUNDS>` - a compressed log of prior questions and the user's answers (one line per Q&A, no reasoning). The agent uses it to detect whether the latest answer raised new aspects vs. reaffirmed prior ones, and to avoid re-asking what's already settled.

**Research first**: before formulating questions in any round, the agent exhausts filesystem (Glob/Grep/Read), prior pre-flight findings, and web sources when the request mentions external surface. It reports what it checked in `LOOKUPS_PERFORMED`. If the codebase or research already answers a candidate question, drop it.

**Loops are free**: clarification loops refine intent within a step. They do NOT count toward the backward-edge budget.

## Backward-Edge Budget

Cap: **2 cumulative backward edges per task.** Backward edges revisit a prior step; they're distinct from in-step loops.

Counts toward the budget:
- `plan-challenger` verdict `revise` → planner rerun
- `plan-challenger` verdict `reject` → reinterview
- implementer kickback (`plan-patch` | `replan` | `reinterview`)
- re-classify after clarify when scope moves

Does **not** count (separate budget of 2):
- fixer self-heal rounds
- reviewer reruns during self-heal

Does **not** count (free, no cap beyond per-stage limits):
- intent loop (Step 0 Level 2 re-runs)
- clarify loop (Step 3 re-runs)

At the cap, stop and surface state to the user - don't loop silently.

## Input Template Contract

Every agent receives inputs via a tagged-slot template defined in its own definition file. The main agent fills slots verbatim from predecessor output - no paraphrase.

Every template:
- names each required slot with an XML-style tag (e.g. `<CONFIRMED_INTENT>`, `<PREFLIGHT>`, `<APPROVED_PLAN>`)
- states the source agent and the expected content for each slot
- the agent's first step parses required slots; on a missing required slot it emits `INPUT_ERROR: missing <slot>` and stops

Output wrapping: agents emit structured blocks named with XML-style tags that successors reference (e.g. `<APPROVED_PLAN version="N">`, `<CLARIFY_OUTPUT>`). This makes relay mechanical and enables re-injection after compaction.

## Compaction

After compaction, a `SessionStart` hook reads the transcript for the highest-version `<APPROVED_PLAN>`, `<CONFIRMED_INTENT>`, `<CLARIFY_OUTPUT>`, `<CLASSIFICATION>`, and re-injects them into the post-compact session.

What still needs manual preservation in the conversation: current workflow step, gate results so far, unresolved self-heal findings, backward-edge count. Canonical state (intent / plan / classify / clarify) re-injects itself.

Discard: raw exploration output, full file contents already acted on, superseded plans.

## Code Quality
- Use the project's formatter.
- Failing tests → fix the code, keeping assertions and coverage intact.
- Delete dead code: unused functions, stale imports, obsolete files.
- Search for existing patterns before writing new ones. Reuse beats reinvention.
- Improve the area you're touching: dead code, stale abstractions, obvious simplifications.

## Reviewer Contract

Shared rules for every specialized reviewer (correctness, quality, security, performance, accessibility, design-consistency, ux, consistency, structure, reuse). Each reviewer's own file carries only its Criteria list and any specialization - the rest lives here.

### Confidence tagging (reviewer reporting threshold)

Tag each finding `[likely]` or `[unsure]` per the "Confidence Tagging" rules above.

**Reporting threshold:** report `[likely]` findings unconditionally. Report `[unsure]` only when impact is high - correctness, security, or data risk (correctness-reviewer priority tiers 1-2). Skip speculative low-impact findings.

### Standard inputs

Every reviewer receives inputs via a tagged-slot template defined in its own file. Every template defines at minimum:

```
<TOUCHED_FILES>{file paths the implementer modified or created - sourced from implementer's FILES_MODIFIED + FILES_CREATED, or from main-agent session edits on S/M tasks}</TOUCHED_FILES>
```

Reviewers Read those files directly to inspect current state. Reviewers that need more declare the additional slots in their template (acceptance-reviewer: `<CONFIRMED_INTENT>` + `<APPROVED_PLAN>`; structure/consistency/reuse-reviewer: `<APPROVED_PLAN>` for scope judgment; plan-adherence-reviewer: `<APPROVED_PLAN>`).

**First step for every reviewer**: parse required slots. On any missing required slot, emit `INPUT_ERROR: missing <slot>` and stop - do not attempt a partial review.

Main agent fills slots verbatim from predecessor output. No paraphrase.

### Base output format

```
VERDICT: [pass | fail | warn]
FINDINGS:
- [likely|unsure] [file_path:line] - [issue and why it matters]
(empty if pass, max 5 issues, [likely] findings first)
ACTION_NEEDED: [specific fixes, or "none"]
```

A reviewer MAY:
- Add specialized fields before FINDINGS (e.g. `DESIGN_REFERENCES`, `EXAMPLES_COMPARED`).
- Specialize the finding description shape (e.g. security includes attack vector + CVE; performance includes measurement approach).

A reviewer MUST NOT:
- Drop VERDICT.
- Lower the reporting threshold.
- Pad findings to hit a target count. Two real issues beats eight noisy ones.
- Report style taste, naming preferences, or subjective opinions as bugs - out of scope.
- Flag code you don't understand. Ask or skip; don't speculate.
- Frame readability or correctness sacrifices as performance/UX wins.

### Example output (consistency-reviewer)

```
VERDICT: warn
EXAMPLES_COMPARED: src/features/reports/controller.ts, src/features/users/controller.ts
FINDINGS:
- [likely] src/features/items/controller.ts:22 - returns `{ data, meta }` but every other controller returns the bare array. Align with reports/users.
- [likely] src/features/items/service.ts:8 - `get_item` (snake_case) diverges from camelCase used elsewhere in the module.
ACTION_NEEDED: Change return shape to bare array; rename `get_item` to `getItem`.
```
