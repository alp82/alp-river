# Expressing the two-dial router in forge's doctrine prose

Date: 2026-07-25. Resolves [#83](https://github.com/alp82/forge/issues/83) on the [complexity-model build map](https://github.com/alp82/forge/issues/82).

Question: how should the two-axis model locked in [`docs/spec/complexity-model.md`](../spec/complexity-model.md) be *written* into `skills/forge/SKILL.md` so an orchestrator follows it reliably, without bloating the file past the point where it is read carefully?

External evidence for every claim about LLM conditional-following lives in the companion survey, [`prose-conditional-gating-prior-art.md`](prose-conditional-gating-prior-art.md); this document cites it rather than restating it. House style: hyphens only.

---

## Executive summary

- **The ticket's stated fear is the wrong one.** "Written naively that could double the file" assumes lines are the budget. They are not: Anthropic caps a skill body at 500 lines and `SKILL.md` is at 76. A worked draft of the full model lands the file at **88 lines**. Lines were never going to be the failure.
- **The real budget is the number of live conditionals, and the design lands inside the danger band.** RealGuardrails finds if-then guardrail compliance approaching zero between 10 and 20 conditionals in one instruction file, with real-world prompts averaging 5.1. `SKILL.md` carries roughly **12 today and roughly 18 after the edit**. This, not length, is the acceptance risk - and this survey does not resolve it. It graduates a ticket.
- **Distributing each gate to the stage it governs beats a central routing block**, on both the doctrine rules this repo already binds itself to and the external evidence. It also happens to be cheaper: +12 lines against roughly +35 for a central table that restates the stage sequence a second time.
- **Anchor: "separable dials"**, the spec's own phrase, carried verbatim, with the operational mnemonic **SIZE gates the artifacts, RISK gates the adversaries** doing the actual steering at each gate.
- **The re-score is a return-block token pair**, shaped identically to triage's, not a `plan.md` section and not its own artifact.
- **One new structural convention: a fixed `**Gate:**` slot label** opening every conditional stage. It is the scannable-marker discipline the strongest published Anthropic skill uses, and it gives the doctrine-integrity self-audit a mechanical canary.

---

## 1. The anchor

`CLAUDE.md` § "Leitwort usage" wants one named anchor per stage, prefers trained lineage over coinage, and demands one concept keep one name.

**Ruling: keep `separable dials`.** Three reasons, in order of weight:

1. **One concept, one name (rule 3) is decisive here.** The spec already names it that in §2 and §2.5. Renaming it at the doctrine boundary would leave the build ticket reconciling two names for one idea across two documents - the exact drift the rule exists to prevent.
2. **Naming consistency is the documented mitigation for the failure mode this router is most exposed to.** Condition conflation - two independent conditions collapsed into one - is precisely the risk of a two-dial router, and Anthropic's stated fix is terminological: "Choose one term and use it throughout the Skill." Two dials named inconsistently across stages will be read as one dial.
3. Its trained lineage is thin, and that is worth saying plainly. "Dial" carries some adaptive-compute association (`reasoning_effort`, effort dials); "separable" is close to coined. Rule 4 says a forced coinage spends words for nothing.

**So the anchor does not carry the load alone.** The phrase that actually steers behaviour at the point of action is the mnemonic:

> **SIZE gates the artifacts** (plan, tests). **RISK gates the adversaries** (challenge, worker).

This earns its place where "separable dials" does not: it is not a label, it is a lookup the orchestrator can run from memory to know *which dial to read* at any stage. It maps each dial onto a category of stage, which makes the separability self-evident rather than asserted, and it survives compression to eight words. Rule 2 (reinforce at the points where the agent acts) is satisfied by the `**Gate:**` markers of §2, not by repeating the anchor.

**Rejected alternatives:** `risk matrix` has the strongest lineage (ISTQB) but fights the design - the spec explicitly rejected a 9-cell case table, and naming it a matrix invites exactly the nested reading that ComplexBench scores worst (0.626 at depth >= 3 against 0.881 for independent constraints). `blast radius` names only one axis. `proportionate process` describes the outcome, not the stance, and gives the orchestrator nothing to do.

## 2. Table vs. prose, and where the gates live

Two questions turned out to be one. The evidence pulls in opposite directions until you separate *the lookup* from *its location*.

**Location: distributed to the stage, not centralised.** `SKILL.md` is already ordered as the pipeline it describes - Triage, Plan, Challenge, Tests, Implement, Review wave, Fix, Close. Each gate can therefore ride in the section of the stage it governs. Four things favour this over a central router block:

- **The distance finding.** Non-compliance rises as the distance grows between a rule and the point it applies, with the failure shifting from wrong-precedence to rule-never-noticed. A central table sits four sections away from the stage that consumes it.
- **Scope does not generalise.** An "authoritative" band stated once does not silently carry to four dependent stages; the file has to say so at each one. That requirement alone forces per-stage text, at which point a central table becomes a second copy.
- **A rule written twice is a coin flip, not an override.** Anthropic: contradicting rules resolve arbitrarily. Central table plus per-stage restatement means the same band values live in two places, which is a drift hazard and a doctrine-hygiene violation both.
- **Leitwort rule 2** wants the anchor recurring where the agent acts. Distributed gates are that, structurally.

**Lookup form: shape it to the payload.** OpenAI's one stated criterion is that tables suit a reader whose job is to compare or choose among options, which a dial lookup is. But the criterion is about *comparability*, not about pipe characters:

- **One token to one word → one sentence.** The plan lookup (skip / light / full) and the tests trigger are single-clause mappings. A three-row table costs five lines to say what a clause says in one, and adds no comparability the sentence lacks.
- **One token to a multi-clause behaviour → a band-per-line list.** The challenge tiers and the review-wave membership carry real payload per band (spawn set, loop cap, escalation target). Here the list *is* the table form - one row per band, aligned, scannable - without a Markdown table's overhead in a file this terse.

There is no evidence favouring pipe tables over aligned bullets for instruction files; format effects are large but model-specific and non-transferable. So the choice is made on line cost and on the one criterion anyone states, not on a general format claim.

**Fold couplings into the rule they modify; never state them as a later override.** This is the sharpest transferable finding, and OpenAI's own worked fix for this exact shape. Two applications:

- The §2.3 plan floor becomes part of the plan rule - *plan depth is the deeper of the size lookup and the risk floor* - so the size lookup is never read against a paragraph that quietly amends it three lines down.
- The §3.4 rewind exception is stated inside the band-ratchet rule at the Implement stage, not as an override of the KICKBACK behaviour documented elsewhere.

**One new convention: the `**Gate:**` slot label.** Every conditional stage opens with a bolded `**Gate:**` line that is the complete rule for that stage. Adopted from the fixed `**Apply if**:` marker that repeats verbatim five times in Anthropic's Opus 4.5 migration skill, the most scannable convention in any published artifact surveyed. Three things it buys:

1. The orchestrator learns one shape and looks for it, instead of parsing each stage's prose for a hidden condition - the documented counter to silent skip, where above 30% of conditional errors are the condition never being evaluated.
2. It forces each gate to be *complete in one place*, which is what makes the fold-the-coupling rule enforceable rather than aspirational.
3. **It is a cheap canary**, satisfying `CLAUDE.md` § "Doctrine hygiene" check 3: a gated stage missing its marker is mechanically detectable, so the self-audit catches a gate that gets reworded away.

We diverge from the published label (`**Apply if**:` → `**Gate:**`) because forge's stages are gated, not applied, and the doctrine already calls these gates throughout. The discipline the evidence supports is a *fixed, verbatim-repeated* slot label; the specific words are ours.

## 3. What stays in the spec

`CLAUDE.md` § "Doctrine hygiene" demands one canonical home per fact. The division:

| Fact | Home | Why |
| --- | --- | --- |
| Band definitions and the signals that set them | `TRIAGE.md` | The classifier owns the vocabulary it emits. `SKILL.md` consumes tokens; it does not need to know how a band was decided. |
| Which stage fires on which band; the coupling; the ratchet; the rewind trigger | `SKILL.md` | Runtime gates. The orchestrator cannot route without them. |
| Why two axes, the folded-away third axes, the §4 validation table, the migration runbook | `docs/spec/complexity-model.md` | Author-time rationale. Never read during a run. |

**The load-bearing rule: doctrine must be runtime-self-sufficient, so `SKILL.md` should not cross-reference the spec at all.** The whole repo does ship into the plugin cache, so `../../docs/spec/complexity-model.md` would technically resolve - which makes this a discipline call rather than a mechanical impossibility, and worth stating explicitly for that reason. Against it: references more than one level deep from `SKILL.md` risk being partially read, and a gate condition in a file the orchestrator only partially reads may never be seen at all. Sending a running orchestrator to a 250-line decision document mid-route spends context to re-derive what the gate line should already have said. The spec is cited from the CHANGELOG, the commit, and this survey - the human's reading path, not the agent's.

**Consequence for the gate lines:** a gate names its token and never re-defines it. Drafting caught a live instance of this - a first pass restated triage's logic-load definition ("a new branch, loop, or computation") inside the Tests gate, duplicating `TRIAGE.md`. Today's `SKILL.md` already gets this right ("triage's NEEDS-TESTS, or the plan reveals it") and the edit must not regress it.

## 4. The re-score's shape

Spec §2.4 leaves the form open. Three candidates:

| Option | Verdict |
| --- | --- |
| A `## Bands` section inside `plan.md` | **No.** The spawn contract passes paths, not content - the orchestrator is not guaranteed to read `plan.md` at all. A gate whose input sits in a file that may go unread is the silent-skip failure mode by construction. |
| Its own run-dir artifact | **No.** A new file for two tokens, with the same unread-input risk plus a file to keep in sync. |
| **Two lines in PLANNER's RETURN block** | **Yes.** |

**Ruling: `PLANNER.md`'s RETURN block gains `SIZE:` and `RISK:` lines, identical in shape and vocabulary to triage's.** The return block is the one channel the orchestrator provably reads - it is how every other stage's control signal already arrives (`PLAN:`, `DETOUR:`, `VERDICT:`, `KICKBACK:`). One token pair with two emitters and one shape means the orchestrator learns the band contract once.

Two supporting points:

- **Repo precedent exists for the apparent duplication.** `PLANNER.md` already emits the Summary both into `plan.md` and verbatim in its return block, deliberately - artifact of record plus transport. The bands ride the same pattern, so no new convention is invented.
- **Pair it with one forced restatement, and do not mistake it for compliance.** The orchestrator restates the resolved stage set once before spawning anything post-plan. This is Anthropic's checklist pattern, whose stated purpose is that clear emitted steps prevent skipping validation. Its value is *external checkability* - a later stage or the adapter's stop-gate can compare the declared stage set against what actually ran. It is explicitly not evidence of compliance: models recall constraints at 97.3% alongside knows-but-violates rates up to 99%. Asking the orchestrator to restate the gate does not predict that it will honour the gate.

## 5. Does it fit? A worked draft

The full model written out across `SKILL.md`'s Triage-through-Review-wave span, with every ruling above applied:

- **Current span (lines 21-63): 43 lines. Draft: 55 lines. File: 76 → 88.** Roughly +16%, against the ticket's feared doubling.
- It carries all of it: both dials, the plan-floor coupling folded into the plan rule, the planner re-score, the size-keyed wave membership, the risk-keyed worker, the band ratchet, the rewind exception, and two worked band-boundary examples promoted from the spec's §4 table.
- **It reproduces all ten rows of the spec's §4 validation table on inspection** - including both anchors (`minimal`+`routine` → today's short path, `substantial`+`critical` → today's full pipeline) and the `substantial`+`routine` motivating gap. This is an inspection, not the acceptance gate; the build ticket runs the table for real.

The draft is not committed - it is an existence proof for the build ticket, which owns the actual edit. It sits in this session's scratch and is reproduced in the resolution comment on [#83](https://github.com/alp82/forge/issues/83).

**Why it is this cheap:** the file's existing shape does most of the work. Each stage section already opens with a sentence; the gate rides in it. A central router block would have restated the stage sequence a second time to say which stage each band selects - roughly +35 lines for strictly less locality.

## 6. The open risk this survey does not close

**Gate count, counted honestly:**

| | Detour flags | Surface lenses | Returns (DETOUR, KICKBACK, two-strike) | Routing | Total |
| --- | --- | --- | --- | --- | --- |
| Today | 5 | 3 | 3 | 1 (trivial short path) | **12** |
| After the edit | 5 | 3 | 3 | 7 (plan, challenge, tests, wave-by-size, wave-by-risk, ratchet, rewind) | **18** |

RealGuardrails puts real-world instruction files at 5.1 conditionals and finds compliance approaching zero between 10 and 20. **The edit moves `SKILL.md` from the low edge of that band to the high edge.** Three independent vendors prescribe the same remedy at the same threshold - branch in prose up to a point, then split the file.

The rulings above already claw some of this back: folding the plan floor into the plan rule is one gate instead of two; collapsing the spec's seven-row §3.2 escalation table into the single-writer ratchet is one instead of seven; pointing the rewind conjunction at a `challenge-ran` marker file in the run dir turns a remembered state conjunction - the shape most likely to be missed entirely - into a file check. Without those three moves the count is closer to 26.

**What remains undecided is whether 18 is acceptable or whether the routing extracts to a sibling `ROUTING.md`.** That is a sharp question, it is not answerable from this survey's evidence alone (it needs the doctrine-site sweep of [#84](https://github.com/alp82/forge/issues/84) to know what else switches on the band tokens), and it must be settled before the atomic swap of [#86](https://github.com/alp82/forge/issues/86) is drafted. It is charted as its own ticket.

**Two further findings, flagged not resolved:**

- **`elevated`'s autonomous ping-pong is the most expression-expensive element in the spec.** Every other new rule reuses an existing rail (`KICKBACK`, `DETOUR`, the user gate). The §2.2 `elevated` band introduces an autonomous planner↔challenger loop with a 2-round cap and an escalation target, and no such loop exists in today's doctrine. Loop-bearing prose rules are where policy-following agents are least consistent - tau-bench reports pass^8 under 25% for state-of-the-art function-calling agents on prose policy. This is a locked model decision (#73) and is not reopened here; it is named as the element most likely to need a deterministic backstop.
- **Which gates deserve enforcement rather than prose.** Anthropic is unambiguous that instructions are advisory and hooks are deterministic, and the interventions with the largest measured effects all move the check outside the model being checked (+12.4 points on tau-bench airline for deterministic pre-execution gates). forge's adapter already runs hooks. The candidates worth weighing are the ACCEPTANCE floor, the critical-risk user sign-off, and the rewind trigger. Out of scope for the doctrine edit; worth its own decision later.

---

## Rulings, condensed

For the build ticket to execute against:

1. Anchor is `separable dials`, carried verbatim from the spec; the steering phrase at each gate is *SIZE gates the artifacts, RISK gates the adversaries*.
2. Gates distribute to the stage section they govern. No central routing block.
3. Every conditional stage opens with a fixed `**Gate:**` line that is the complete rule for that stage. The self-audit gets it as a canary.
4. Single-clause lookups are sentences; multi-clause lookups are one line per band. No pipe tables in `SKILL.md`.
5. Couplings fold into the rule they modify. Nothing is stated as a later override of an earlier rule.
6. Gate lines name a token and never re-define it. Band definitions stay in `TRIAGE.md`.
7. `SKILL.md` does not cross-reference the spec. Doctrine is runtime-self-sufficient.
8. The re-score is `SIZE:` / `RISK:` lines in `PLANNER.md`'s RETURN block, shaped like triage's, plus one restatement of the resolved stage set before post-plan spawns.
9. The rewind trigger reads a `challenge-ran` marker in the run dir, not a remembered conjunction.
10. Phrase gates affirmatively and do not escalate emphasis; ALL-CAPS is a yellow flag in Anthropic's own authoring skill, and over-triggering is a documented cost of aggressive language.
