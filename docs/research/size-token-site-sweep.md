# Size-token site sweep - every doctrine site the two-axis swap touches

Question: what is the complete set of files that switch on the `trivial | standard` size token, and has anything moved under the spec since it was locked?

Method: repo-wide grep for the band literals (`trivial`, `standard`, `SIZE`, `NEEDS-TESTS`), for review-wave lens membership (the five standing lens names, `findings-`), and for the stage-gate prose that the new model makes conditional; then a read of every hit in context. Scope was `skills/`, `adapters/`, `scripts/`, plus `.claude/`, `docs/spec/`, `demo/`, and the root docs, since the sweep's purpose is "no half-migrated pipeline" rather than a directory boundary. Swept at `a7c0999`, forge 2.2.3.

**Headline:** spec §5.2's "three contained edit sites" is incomplete by three. The atomic swap spans **four** files under `skills/forge/`, not three - `PLANNER.md` is the authoritative writer of both bands per §2.4/§3.1 and its RETURN block has no SIZE/RISK line today. Two further sites sit outside the swap. The enforcement layer is clean in all three adapters, and both §4 anchors verify against the files as they currently stand.

---

## 1. The site list

### Tier A - the atomic swap (must land in one change)

| # | Site | Lines | What it carries | In §5.2? |
|---|---|---|---|---|
| A1 | `skills/forge/TRIAGE.md` | 16-17, 19, 34 | Band definitions (`trivial`/`standard`); `NEEDS-TESTS` with its `trivial` implies `no` clause; the RETURN block's `SIZE: trivial \| standard` line | yes |
| A2 | `skills/forge/SKILL.md` | 23, 31, 33-35, 37-44, 48, 55, 57-63 | Every live gate (below) | yes |
| A3 | `skills/forge/IMPLEMENTER.md` | 3 | "On the trivial short path there is no plan" -> "when no plan ran" | yes |
| A4 | `skills/forge/PLANNER.md` | 54 | RETURN block gains the authoritative `SIZE:` / `RISK:` re-score lines | **no** |

**A2 in detail.** §5.2 calls SKILL.md "the gating" as if it were one block; concretely it is seven distinct spots:

- `:23` - triage spawn, "returns size and flags" (the consumption point for the new token pair).
- `:31` - the **Trivial short path** block, the only explicit size switch in the file.
- `:33-35` - **Plan**, currently ungated. Becomes the §2.1 size lookup plus the §2.3 risk floor.
- `:37-44` - **Challenge**, currently ungated and unconditionally HITL. Becomes the §2.2 risk tier, including `elevated`'s autonomous planner<->challenger ping-pong capped at 2 rounds.
- `:48` - **Tests**, already gated on `NEEDS-TESTS`; §2.1 keeps the trigger and adds the re-gate on the re-scored SIZE.
- `:55` - "a forward correction, no re-gate through the challenge". This is the exact line §3.4's rewind exception overrides.
- `:57-63` - **Review wave** membership: `:61` the five standing lenses, `:62` the three conditionals, `:63` the worker. §2.5 makes `:61` size-keyed and moves the worker to critical-only; `:62` is unchanged (surface-triggered, dial-independent).

**A4 - the omission that matters.** §2.4 makes the planner the authoritative scorer and §3.1 makes it the *single writer* of both axes; the escalation table at §3.2 routes every other stage's raise through a planner re-spawn. `PLANNER.md:54` returns only `PLAN: <path> v<N>` or `DETOUR: prototype`. If A4 does not ride the same change, SKILL.md gates tests, challenge, and review depth on a re-score that is never emitted, and the orchestrator silently falls back to triage's provisional call for every post-plan gate - the half-migrated pipeline this sweep exists to prevent. Independently confirmed by the doctrine-expression survey (#83), which ruled the re-score into this exact block.

### Tier B - real sites, outside the atomic swap

| # | Site | Lines | Exposure | In §5.2? |
|---|---|---|---|---|
| B1 | `skills/crossfire/SKILL.md` | 21-23 | Its own standing-lens list, duplicating forge SKILL.md `:61`. Crossfire runs without triage, so it has no band to key off | no |
| B2 | `skills/forge/CHALLENGER.md` | 43 | "The orchestrator carries the Approve/Revise/Reshape gate to the user" - stated unconditionally. False at `elevated`, where §2.2 makes the loop autonomous and the human appears only on the 2-round cap | no |
| B3 | `docs/spec/adapter-contract.md` | 338-342 | Conformance checklist item 4 drives a **trivial** task and names the short-path stage set ("TRIAGE -> IMPLEMENTER -> the review wave without the plan/challenge/test gates"). The band literal disappears; the stage set survives as `minimal + routine` | no |
| B4 | `skills/forge/SKILL.md` frontmatter | 3 | The `description` enumerates "triage, plan, challenge, implement test-first, review wave, fix" as a flat list. Model-facing routing text since `a7c0999`; post-swap it describes the maximal path, not the path | no - see §3 |

B1 is the one that needs a *decision* rather than an edit: the map already carries it as an open fog patch, and the reconcile ticket owns it. Note the coupling if it is ruled in - `skills/crossfire/SKILL.md:25` ("SECURITY is trigger-gated, so CORRECTNESS's injection checks are the only injection coverage") is the same argument §2.5 uses to keep conditionals dial-independent, so a scaled crossfire wave must preserve it.

B2 and B3 are one clause each. B4 is optional and non-blocking - a routing hint, not a gate - but the atomic-swap commit is the cheap place to soften it.

`adapter-contract.md:343-348` (item 5, "at least one `findings-<lens>.md`, `findings-correctness.md` always rides the wave") **survives untouched**: CORRECTNESS is the §2.5 floor in every cell.

### Tier C - peripheral, non-blocking

- `demo/playbooks/hero.play:13`, `demo/playbooks/stage-triage.play:10` and their recorded casts (`demo/casts/hero.cast:69`, `demo/casts/stage-triage.cast:68`) render `SIZE standard`, a band that ceases to exist. User-visible via the README hero gif. A demo-regeneration task, not part of the swap.
- `CHANGELOG.md:160, 247, 344` mention `trivial` in shipped-release history. Never edited.

### Verified clean - not sites

- **All hooks, all three adapters.** Zero occurrences of `SIZE`, `trivial`, or any lens name. `adapters/opencode/` has no lens or routing references at all (`forge.js` carries only the version stamp).
- **All hook test suites.** `findings-correctness.md` appears only as a sample fixture filename (`test_review_owed.py:86,113,143,283,334`; `test_mark_code_change.py` TC-MCC-13/14). No test asserts a lens set or a lens count; any `findings-*.md` satisfies every one of them.
- **`scripts/`** - `version_mirrors.py` and `bump-version.py` handle version strings only.
- **`.claude/skills/`** (audit, reflect) - one incidental "the review wave" as an example argument-hint. No membership, no bands.
- **`docs/spec/forge.md:125`** - a file inventory of the five lens briefs. All five briefs survive the swap; only *when they fire* changes.
- **`README.md`** - settled by spec §6: the wave scales but never empties, and the stage table describes behavior-when-run. Nothing becomes false.
- **`skills/forge/FIXER.md:25-27`** - the RERUN set is "lenses whose findings you fixed", membership-agnostic by construction.
- **`skills/forge/WORKER.md`** - parameterized by call site (`challenge` / `crossfire`), membership-agnostic.

---

## 2. Enforcement-layer exposure

**Verdict: the enforcement layer is indifferent to wave size, in both adapter copies. Shrinking the wave cannot break the Stop gate.**

- `adapters/claude-code/hooks/review-owed.py:84` and `adapters/codex/hooks/review-owed.py:87` both settle the debt with `forge.rglob("findings-*.md")` - any single file newer than the change marker settles, regardless of which lens wrote it. The two copies are non-identical in docstring and layout but identical in this predicate.
- The §2.5 floor is CORRECTNESS + ACCEPTANCE in every cell, so the thinnest possible wave still writes two findings files. The gate cannot be starved by routing.
- `mark-code-change.py` is INERT on `.forge/` run-dir writes in both adapters (TC-MCC-13), so lens output never arms a fresh debt - the wave size has no effect on debt creation either.
- No hook, and no hook test, encodes an expected lens set or count. Charting's finding for the claude-code copy holds for the codex copy.

---

## 3. Drift since the spec was locked

The spec was assembled at `c587af2` (2026-07-22). `a7c0999` (2026-07-24) is the only commit since.

1. **`skills/forge/SKILL.md` and `skills/crossfire/SKILL.md` were touched in frontmatter only.** Both bodies are byte-identical to what the spec described. §5.2's SKILL.md edit surface and crossfire's `:21` standing-lens list are exactly as charted. No re-scoping needed.
2. **The review-owed per-debt cap fix is orthogonal to routing.** It changed *when* the gate blocks (once per debt, settling before the `stop_hook_active` short-circuit), not *what* settles it. The `findings-*.md` predicate is untouched. No spec assumption invalidated; the degenerate case named in its docstring (a never-settled debt silences the gate for the session) is unaffected by wave size.
3. **One genuine gap the spec could not have anticipated.** Dropping `disable-model-invocation: true` promoted `/forge` and `/crossfire` to the model-invoked tier, which made their frontmatter `description` fields **model-facing routing text**. Spec §6 audited the README's public claims but predates this change, so no analysis covers the descriptions. forge's now reads as a flat unconditional stage list; post-swap that is the maximal path. Low severity - it steers *whether* forge is entered, never which stages fire - but it is the one place where `a7c0999` widened the surface §6 signed off on. Filed above as B4.
4. **`docs/spec/forge.md`'s "two tiers" amendment** carries no routing dependency.

---

## 4. The §4 validation-table anchors, checked against the files as they stand

### Row 1 - `minimal + routine` reproduces today's trivial short path: **verified**

Today, `skills/forge/SKILL.md:31`: skip plan, challenge, and tests; IMPLEMENTER at tier `ultra` straight off `intent.md`; "run the wave with CORRECTNESS plus any triggered conditional lens."

Spec row 1: skip / no / none / CORRECTNESS + ACCEPTANCE.

Pipeline shape matches exactly. Two details worth pinning:

- The `+ACCEPTANCE` delta is the documented refinement at spec §196, not a discrepancy.
- Today's short path also excludes the **worker** lens - `:31` names only CORRECTNESS plus conditionals, never `:63`'s worker. Spec row 1 has no worker either (worker is critical-only per §2.5). This half of the anchor holds silently and is worth keeping that way.

### Row 10 - `substantial + critical` reproduces today's full pipeline: **verified, exact**

Today's `standard` path: PLANNER full (`:33-35`), tests when `NEEDS-TESTS` (`:48`), CHALLENGER + WORKER in parallel with the HITL Approve/Revise/Reshape gate (`:37-44`), wave = five standing lenses (`:61`) + surface conditionals (`:62`) + the worker lens (`:63`).

Spec row 10: full / yes / challenger+worker+HITL / floor + CONVENTIONS + SIMPLICITY + SHAPE + worker.

Set-identical: {CORRECTNESS, ACCEPTANCE} ∪ {CONVENTIONS, SIMPLICITY} ∪ {SHAPE} ∪ {worker} is exactly `:61` plus `:63`.

One nuance to record so the acceptance gate does not misread it: today's `standard` also fires the challenge and its HITL gate at cells the new model calls `moderate × routine`. That is not an anchor failure - it is precisely the "not-trivial => fire everything" blob §5.1 says dissolves into active grid placement.

---

## 5. What this changes for the build

1. **The atomic set is four files, not three.** `TRIAGE.md` + `SKILL.md` + `IMPLEMENTER.md` + `PLANNER.md`. Spec §5.3's coupling argument extends verbatim to A4: SKILL.md cannot gate on a re-score the planner does not emit.
2. **§5.2 needs amending**, per the map's "the spec is law" note - the build ticket amends `docs/spec/complexity-model.md` §5.2 to name PLANNER.md as a fourth site rather than routing around the omission.
3. **Two one-clause follow-ons** ride outside the swap: `CHALLENGER.md:43` and `adapter-contract.md:338-342`.
4. **Gate budget (#88) is unaffected in kind.** A4 adds an *emission* to PLANNER.md, not a conditional to SKILL.md, so the survey's 12 -> 18 gate count for SKILL.md stands as measured.
5. **The enforcement layer needs no change and no test change.** That question is closed.
