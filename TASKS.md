SWOT assessments

multiple angles - Design It Twice

less to read

push for 100% validation for goals

TDD

complexity worth it?
```
Two gates, different questions:

1. Top-level "should we do this at all?" - after `complexity-classifier`, before
   clarify/plan. Fires only on L|XL. Output asks the user a one-line value-vs-cost
   prompt with the classifier's REASON inline, e.g.
     "Classified XL (5+ files, new module). Cost: ~30min planning + full quality
      gates. Worth it, or scope down? [y / scope down / abandon]"
   - "y" continues the pipeline
   - "scope down" loops back to interviewer with a "reduce scope" directive
   - "abandon" stops cleanly
   Lives in `/feature` and `/plan` commands. Skip on `/fix` (S|M already cheap).

2. Plan-level scope-vs-value check - new finding category inside
   `plan-challenger`. Currently it flags per-component over-engineering
   ("abstractions not justified by requirements"). Add a whole-plan check: does
   the plan's total surface (file count, new modules, new seams) match the
   stated intent's leverage? Findings emit as `SCOPE_MISMATCH` alongside
   existing BLOCKERS/CONCERNS, with a one-line "drop X to land Y" suggestion.

Open: should (1) be a hard gate (block until answered) or soft (show + continue
after default)? Hard avoids drift, soft preserves flow. Lean hard for XL, soft
for L.
```

use Aristotelian first principles reasoning. before you proceed, break every undefined term down to its atomic meaning
```
  1e: Aristotelian first principles - where it fits

  Your reddit quote: "use Aristotelian first principles reasoning. before you proceed, break every undefined term down to its atomic 
  meaning"

  The phrase works because LLM agents drift on fuzzy terms. "Improve the auth", "modernize the dashboard", "clean up X" - the verbs are
  placeholders for unspecified intent, and downstream agents act on the assumed meaning instead of asking. Decomposition forces the
  assumption to surface.

  Three places it integrates naturally:

  1. Interviewer (Step 0 Level 2) - highest leverage. Before formulating any question, the interviewer should identify fuzzy terms in
  <RAW_REQUEST> and <L1_CONFIRMATION>, decompose each to atomic meaning, and surface ambiguity that way. Today interviewer asks "what's
  the priority trade-off?" - with this, it asks "you said 'improve' - do you mean faster, more secure, more readable, or feature-richer?
  Each implies different work."
  2. Clarifier (Step 3) - second leverage point. Same decomposition pattern, applied to <CLARIFY_OUTPUT> candidate questions. If a
  question contains a fuzzy term, decompose before asking.
  3. Planner (optional) - decompose "build the X" into atomic actions before sequencing. Catches design assumptions like "build the queue"
   - one queue per user? Per tenant? Per topic?

  How to phrase in the prompts:

  A dedicated process step early in interviewer and clarifier:

  ▎ Decompose before asking. Identify every fuzzy or jargon-laden term in your inputs. For each, write its atomic meaning. A term 
  ▎ qualifies as fuzzy when ANY of these hold: (a) two reasonable readings produce materially different work, (b) the term is 
  ▎ project-specific jargon not in GLOSSARY.md, (c) the term bundles multiple concerns ("improve", "modernize", "clean up") without 
  ▎ specifying which. Stable code/tech vocabulary (function, repository, endpoint) does not qualify. If decomposition surfaces ambiguity, 
  ▎ that becomes the question - prefer it over downstream surface questions.

  Risk to manage: "philosophy theater" - long preamble decomposing obvious terms. The qualifier list above is the guardrail. Plus a hard
  rule: decomposition appears in LOOKUPS_PERFORMED output (the existing slot for showing recon), not as a separate verbose block.

  This pairs naturally with the existing "research first" rule. Decomposition identifies which terms need clarification; research checks
  if the codebase already answers them; only what remains becomes a question.

  Pair this with the user's other 1e items: recommend-an-answer per question (already planned) + concrete scenario probing +
  cross-reference user statements against code. The Aristotelian framing slots in at the front of all of them.
```

investigator: diagnose improvements
```
1h: Diagnose discipline - how to build

  Matt's diagnose has 6 phases. Current alp-river investigator has 7 steps. Side-by-side, the gaps:

  ┌──────────────────────────────────┬──────────────────────────┬─────────────────────────────────────────────────────────────────────┐
  │           Matt's phase           │   alp-river equivalent   │                                 Gap                                 │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 1. Build feedback loop (10-rung  │ (not present)            │ Missing entirely - alp-river jumps to repro                         │
  │ ladder)                          │                          │                                                                     │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 2. Reproduce                     │ Step 4 minimal repro     │ Matt frames as binary "did the loop produce the bug" - alp-river is │
  │                                  │                          │  severity-gated                                                     │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 3. Hypothesize (3-5 ranked,      │ Step 2 hypotheses (2-4   │ Falsifiability - alp-river says "dismiss with evidence", Matt says  │
  │ falsifiable)                     │ ranked)                  │ "state the prediction"                                              │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 4. Instrument ([DEBUG-xxxx]      │ (implicit)               │ Tagging discipline missing                                          │
  │ tags)                            │                          │                                                                     │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 5. Fix + regression test (seam   │ Step 6 recommend fix     │ Regression test / seam adequacy missing                             │
  │ check)                           │                          │                                                                     │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ 6. Cleanup + post-mortem         │ (not present)            │ Missing entirely - investigator stops at diagnosis                  │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ (none)                           │ Step 3 web cross-check   │ alp-river has this, Matt doesn't - keep                             │
  ├──────────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ (none)                           │ Step 7 classify          │ alp-river has this for routing - keep                               │
  │                                  │ complexity               │                                                                     │
  └──────────────────────────────────┴──────────────────────────┴─────────────────────────────────────────────────────────────────────┘

  Concrete build path (do these in order, each is its own slice):

  1. Add Phase 0: feedback loop construction. Investigator's first action is naming the loop that will reveal the bug. Matt's 10-rung
  ladder gets embedded in the prompt (failing test → curl → CLI fixture → headless browser → trace replay → harness → property/fuzz →
  bisection → differential → HITL). Investigator picks one, justifies why higher rungs don't apply.
  2. Force falsifiability on hypotheses. Each hypothesis must include a prediction: "If [X] is the cause, then [Y] will make the bug
  disappear / get worse." Non-falsifiable hypotheses get rejected by the agent's self-check before output.
  3. Add [DEBUG-xxxx] tagging. Investigator's instrumentation guidance: every debug log uses a unique 4-char prefix so cleanup is one
  grep. Tagged logs are listed in a new output slot INSTRUMENTATION_PLACED.
  4. Add CLEANUP_NEEDED output. Investigator emits a list of things to clean before declaring done: debug instrumentation, throwaway
  prototypes, temp files. Fixer reads this in subsequent /fix runs.
  5. Add seam-adequacy flag. If the investigator concludes the bug can't be locked down with a regression test at a correct seam, surface
  ARCHITECTURAL_FRICTION with the specifics. Feeds future /improve-codebase-architecture work.

  Cost: investigator goes from ~80 lines to ~200. Worth it - it's already opus, runs only on hard bugs via /investigate, and currently
  produces relatively shallow diagnoses given its model tier.

  Risk: ceremony on simple bugs. Mitigation: the loop-construction phase outputs "feedback loop: trivial - failing test at X" when it's
  obvious. The structure is available not mandatory for every phase.
```


visual reviewer opt-in: only when user confirms

better browser automation
```
Why the browser session was rough                                                                    The investigator subagent ran a Playwright/Chromium probe to confirm the hit-test theory. A few things compounded on  
  it:                                                                                   
  1. No standing browser instance. Each agent invocation starts cold — install/launch Chromium, navigate to dev server, 
  set up event listeners, scroll, probe, tear down. Most of the wall-clock time is setup, not the actual probe.       
  2. Hit-testing is genuinely tricky to verify from CSS alone. Stacking-context behavior with position: fixed parents   
  that hold their own z-index is a footgun — the spec says child z-index is scoped to the parent's stacking context, but
   it reads like child z-index ranks against the document. The only way to be 100% sure was to ask the browser "what's
  actually at this pixel?" via elementsFromPoint and getComputedStyle. That requires a real browser.                    
  3. Multiple scroll positions to test. The investigator probed at scroll fractions 0.5, 0.75, 0.9, 1.0 to also rule out
   H5 (dig never reaches viewport) — which it confirmed was in viewport, just under <main>. Each scroll + probe is its  
  own round trip.
  4. elementsFromPoint + computed-style inspection serialized. The probe couldn't parallelize easily because each step  
  depends on the prior (scroll → wait for paint → query → assert).                                                      
                                         
  Net: the subagent went deep to give a definitive answer rather than a "probably this," and it earned a clear repro + a
   clean refutation of three other hypotheses. But the duration was much higher than the actual fix size warranted.   
                                
  Cheaper option for next time: skip the headless probe for CSS hit-test bugs and reason from spec + a one-line manual  
  test ("set main { pointer-events: none } in DevTools, does it work?"). Faster and almost as conclusive. I should have
  biased toward that given how localized the symptom was.      
  ```