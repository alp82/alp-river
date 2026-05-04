better browser automation
```
Why the browser session was rough                                                                                     
                                                                                                                
  The investigator subagent ran a Playwright/Chromium probe to confirm the hit-test theory. A few things compounded on  
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