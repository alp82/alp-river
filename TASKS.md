setup invisible

SWOT assessments

multiple angles
* multiple prototypes
* Design It Twice

push for 100% validation for goals
* TDD
* other validations

XXL --> too big + pushback or explicit treating as XL


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