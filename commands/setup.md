---
description: Set up project-context docs (INTENT/STACK/GLOSSARY) in docs/ via guided interview
argument-hint: ""
---

# Project-Context Setup

Bootstrap `docs/INTENT.md`, `docs/STACK.md`, and `docs/GLOSSARY.md` for this project. The flow is a 5-invocation interview driven by `setup-agent`. Agent does the recon and drafts; the user picks per-file actions and answers a small batch of questions per file.

**No backward edges in this flow.** The interview is capped at 5 invocations and the write phase is unconditional - if a question goes unanswered by Inv 5, the agent fills with best inference and reports it.

## Step 1: Recon (Inv 1)

Launch `setup-agent`:

```
<INVOCATION>1</INVOCATION>
<PRIOR_ROUNDS>none</PRIOR_ROUNDS>
<RECON>none</RECON>
<USER_ANSWERS>none</USER_ANSWERS>
<EXISTING_DOCS>{paths under docs/ that exist with first 40 lines each, or "none" - you supply this from a quick Glob+Read pass; agent will also re-read directly}</EXISTING_DOCS>
<PER_FILE_ACTIONS>none</PER_FILE_ACTIONS>
```

The agent returns `RECON`, `EXISTING_DOCS_BODIES`, `PER_FILE_ACTIONS_RECOMMENDED`, `GREP_CANDIDATES`, and `READS_TO_PREP` plus an `<INIT_RESULT>` with `NEXT_PHASE: per-file-action-decision`.

## Step 2: Per-file action decision

Present the agent's `PER_FILE_ACTIONS_RECOMMENDED` to the user along with a brief recon summary (detected language, framework, runtime). Format the choice so it's easy to confirm:

```
INTENT: recommend <action> - <reason>. Options: create | merge | skip
STACK:  recommend <action> - <reason>. Options: create | merge | skip
GLOSSARY: recommend <action> - <reason>. Options: create | merge | skip
```

Capture the user's per-file choices and assemble `<PER_FILE_ACTIONS>` as `INTENT=<action>; STACK=<action>; GLOSSARY=<action>`.

If all three are `skip`, tell the user there's nothing to do and end the command (emit `<!-- pipeline-complete -->`).

## Step 3: INTENT prep + answer (Inv 2)

If `INTENT=skip`, skip this step.

Otherwise launch `setup-agent` with:

```
<INVOCATION>2</INVOCATION>
<PRIOR_ROUNDS>none</PRIOR_ROUNDS>
<RECON>{full RECON block from Inv 1}</RECON>
<USER_ANSWERS>none</USER_ANSWERS>
<EXISTING_DOCS>{EXISTING_DOCS_BODIES from Inv 1}</EXISTING_DOCS>
<PER_FILE_ACTIONS>{user's choices from Step 2}</PER_FILE_ACTIONS>
```

Present the returned `QUESTIONS` to the user as a numbered list. Each question carries a `Recommendation` and `Source`; allow the user to answer with `accept`, `edit: ...`, or `reject` per question. Capture the answers in compressed form (`Q1: accept`, `Q2: edit: ...`, etc.) for `<USER_ANSWERS>` on Inv 5.

## Step 4: STACK prep + answer (Inv 3)

If `STACK=skip`, skip this step.

Otherwise launch `setup-agent` with:

```
<INVOCATION>3</INVOCATION>
<PRIOR_ROUNDS>{compressed Inv 2 Q&A, or "none" if INTENT was skipped}</PRIOR_ROUNDS>
<RECON>{full RECON block from Inv 1}</RECON>
<USER_ANSWERS>{Inv 2 answers if INTENT prep ran, else "none"}</USER_ANSWERS>
<EXISTING_DOCS>{EXISTING_DOCS_BODIES from Inv 1}</EXISTING_DOCS>
<PER_FILE_ACTIONS>{from Step 2}</PER_FILE_ACTIONS>
```

Present `QUESTIONS` per layer; capture answers the same way.

## Step 5: GLOSSARY prep + answer (Inv 4)

If `GLOSSARY=skip`, skip this step.

Otherwise launch `setup-agent` with:

```
<INVOCATION>4</INVOCATION>
<PRIOR_ROUNDS>{compressed Inv 2-3 Q&A}</PRIOR_ROUNDS>
<RECON>{full RECON block from Inv 1}</RECON>
<USER_ANSWERS>{Inv 3 answers if STACK prep ran}</USER_ANSWERS>
<EXISTING_DOCS>{EXISTING_DOCS_BODIES from Inv 1}</EXISTING_DOCS>
<PER_FILE_ACTIONS>{from Step 2}</PER_FILE_ACTIONS>
```

Present the user-named-terms prompt and the grep-candidate triage list. Capture answers.

## Step 6: Write (Inv 5)

Always run, regardless of how many earlier prep steps were skipped. Launch `setup-agent` with all collected answers:

```
<INVOCATION>5</INVOCATION>
<PRIOR_ROUNDS>{compressed full Q&A from Inv 2-4}</PRIOR_ROUNDS>
<RECON>{full RECON block from Inv 1}</RECON>
<USER_ANSWERS>INTENT: {answers or "skipped"}; STACK: {answers or "skipped"}; GLOSSARY: {answers or "skipped"}</USER_ANSWERS>
<EXISTING_DOCS>{EXISTING_DOCS_BODIES from Inv 1}</EXISTING_DOCS>
<PER_FILE_ACTIONS>{from Step 2}</PER_FILE_ACTIONS>
```

The agent writes the files (or `.proposed` siblings on divergent merges) and returns `WRITES` + `REPORT`.

## Step 7: Present result

Show the user the agent's `WRITES` and `REPORT` blocks verbatim. Highlight:

- Any best-inference fills they should review
- Any `.proposed` siblings that need merging or deleting
- Any per-file failures

End with the literal line `<!-- pipeline-complete -->` (HTML comment, invisible to the user).
