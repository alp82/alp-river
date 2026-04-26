---
description: Systematic root-cause debugging. Stops at diagnosis — does not patch.
argument-hint: Describe the bug, the symptom, or the unexpected behavior
---

# Investigate Pipeline

Bug report: $ARGUMENTS

Diagnosis only. STOPS at a root-cause report. Applying the fix is a separate step via `/fix` (S/M) or `/feature` (L/XL).

**USER_CONTEXT** auto-injects via the PreToolUse(Agent) hook.

## Step 1: Confirm framing

Restate in one sentence what you understand the bug to be — observed vs expected vs environment. Flag critical missing info (error text, exact command, version, data shape). **Wait for user confirmation or the missing info.** Do not proceed on guesses.

## Step 2: Investigate

Launch `investigator`:
- Input: `<BUG_REPORT>` (user's original report), `<FRAMING>` (your Step 1 restate + any supplied missing info).

The investigator self-assesses SEVERITY (low/medium/high/critical, drives the repro bar) and COMPLEXITY (S/M/L/XL, drives routing). Severity high/critical requires a repro; low/medium allows hypothesis-only when repro is impractical.

It reads code, forms hypotheses, attempts minimal repro, traces to root cause. Does NOT patch.

## Step 3: Report

Present the investigator's output verbatim to the user:
- VERDICT
- SEVERITY + COMPLEXITY
- Root cause (if found) or the strongest remaining hypothesis
- RECOMMENDED FIX
- MISSING_INFO if any

## Step 4: Handoff

Route by the investigator's `COMPLEXITY` field:
- **S/M** → "Run `/fix` with this report."
- **L/XL** → "Run `/feature` with this report."
- `VERDICT: cannot-diagnose` → surface MISSING_INFO and wait.

Do NOT implement the fix inside this command.

**From this point forward**: every subsequent request in this conversation is a new task. Classify it (S/M/L/XL), run the appropriate pipeline.
