---
description: Manually draft and write an architectural decision record. Three steps - confirm input, run the shared ADR Drafter Loop, summarize.
argument-hint: Decision title and a one-line summary (e.g. "use HTTP-only cookies for auth - rules out JWT-in-localStorage")
---

# ADR Pipeline

Manual entry: `$ARGUMENTS`

Use this when you want to record a decision deliberately. The shared **ADR Drafter Loop** (defined in `AGENTS.md`) does the drafting, presenting, and writing - this command is the user-driven entrypoint that prepares one input from `$ARGUMENTS`. Auto-captured ADRs from `/alp-river:feature` (Step 10) and `/alp-river:fix` (Step 8) runs invoke the same loop with entries from the capture pipeline.

## Step 1: Confirm input

Parse `$ARGUMENTS` into a title and a one-sentence summary. If either is missing or ambiguous, ask the user one question to resolve it - keep this short. Do NOT enter the interview loop here; this is a deliberate entrypoint and the user has already framed the decision.

If `docs/adr/` does not exist:
- If `docs/` itself is missing: tell the user "docs/ not found - run `/alp-river:setup` first to bootstrap project context, then re-run this command." **STOP.**
- If `docs/` exists but `docs/adr/` does not: create `docs/adr/` (mkdir). One write, no scaffolded files.

Capture:
- `<DECISION_TITLE>` - the short title.
- `<DECISION_SUMMARY>` - 1-3 sentences capturing the choice and the constraint it locks in.
- `<SOURCE>` - "manual /alp-river:adr entry by user on {today YYYY-MM-DD}".
- `<EXTRA_CONTEXT>` - if the user supplied anything beyond title + summary, include it here verbatim; else "none".

## Step 2: Run the ADR Drafter Loop

Run the **ADR Drafter Loop** (see `AGENTS.md` → ADR Drafter Loop) with the four input slots from Step 1.

The loop drafts via `adr-drafter`, presents the draft + contradiction check + self-criticism to the user, then writes on `accept`/`edit` or stops on `reject`. On `rejected` from the drafter (duplicate of an active ADR), the loop surfaces `ADR_REJECTED` and stops - this command exits without writing. The user can then edit the existing ADR manually or re-run with a re-framed title.

After the loop returns, capture: did it write a file? Was it rejected by the drafter? Was it rejected by the user? Carry that into Step 3.

## Step 3: Summarize

Report:

- ADR created: `docs/adr/NNNN-{kebab-title}.md`
- Status: proposed
- Source: manual entry
- Warnings (if any from self-criticism): list them so the user knows what to revisit later
- Contradictions (if any): list with the file/section that conflicts

End with the literal line `<!-- pipeline-complete -->`.
