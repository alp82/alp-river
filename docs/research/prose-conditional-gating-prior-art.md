# Prose-driven conditional stage gating: prior-art survey

Date: 2026-07-25.

Question: how do prose-driven agent pipelines express conditional stage gating that an LLM has to execute reliably, and what fails? forge is about to replace a binary `SIZE: trivial | standard` router with two independent dials (`SIZE: minimal|moderate|substantial` x `RISK: routine|elevated|critical`), each gating different stages, plus one cross-dial coupling, a mid-pipeline planner re-score, an escalation table, and a bounded rewind exception - all of it written into `skills/forge/SKILL.md`, a 76-line Markdown file that an orchestrator LLM reads and follows. The risk is doctrine the orchestrator misreads shipping the wrong stage set.

This feeds the complexity-model build (spec: [`docs/spec/complexity-model.md`](../spec/complexity-model.md); routing prior art: [`docs/research/complexity-routing-prior-art.md`](complexity-routing-prior-art.md)).

Primary sources only for load-bearing claims: vendor documentation (Anthropic, OpenAI, Google, GitHub, Cursor, Microsoft), actual published source artifacts (`anthropics/skills`, `anthropics/claude-code`, `github/docs`, framework repos), and arXiv papers. Secondary write-ups were not used. Pages that drift carry a fetch date; every vendor page below was fetched **2026-07-25** unless noted. Items that could not be confirmed against the source that owns them are labeled `[unverified]`; figures taken from a paper's HTML rather than re-read off its PDF are labeled `[html]`, because HTML extraction garbled two load-bearing tables during this survey and PDF reads corrected both. House style: hyphens only.

## Executive summary

- **Every vendor documents a conditional-instruction pattern, and every vendor also documents the point at which you should stop writing conditionals.** Anthropic ships a "Conditional workflow pattern" template and then says: "If workflows become large or complicated with many steps, consider pushing them into separate files." OpenAI: "When prompts contain many conditional statements (multiple if-then-else branches), and prompt templates get difficult to scale, consider dividing each logical segment across separate agents." Google: "Instead of having many instructions in one prompt, create one prompt per instruction." Three independent vendors, one shape: branch in prose up to a threshold, then restructure.
- **The measured threshold is far lower than anyone's line budget suggests.** Anthropic and Cursor independently cap instruction files at 500 lines, but the binding constraint is the *number of conditionals*, not lines. RealGuardrails ([arXiv:2502.12197](https://arxiv.org/abs/2502.12197)) stress-tests if-then guardrails in a system message and finds pass rate "quickly approaches zero" between 10 and 20 of them, with real-world prompts averaging 5.1. forge's edited `SKILL.md` will carry roughly 12-15 live conditionals in ~110 lines. That is the number to manage, not the line count.
- **Conditional instructions fail in two separable ways, and the evaluation half is the underrated one.** AgentIF ([arXiv:2505.16944](https://arxiv.org/abs/2505.16944)) splits condition-constraint errors into "incorrect condition checking, where the LLM fails to determine whether a condition is triggered" and "instruction following failure, where the LLM fails to follow the constraint even when the condition is triggered," and finds **above 30% of errors are the first kind**. Attaching a condition to an otherwise-identical constraint costs 15-26 points of satisfaction rate. KCIF ([arXiv:2410.12972](https://arxiv.org/abs/2410.12972)) measures the mirror image: instructions whose condition does *not* apply still cost frontier models 5-20 points - over-firing is real and measurable, not just a worry.
- **Conditional composition specifically is where models fall off.** ComplexBench ([arXiv:2407.03978](https://arxiv.org/abs/2407.03978), NeurIPS 2024 D&B) defines "Selection" as "The output is required to select different branches according to certain conditions, fulfilling the constraints of the corresponding branch" - literal conditional branching. GPT-4-1106 scores **0.881 on And** (multiple constraints at once), **0.765 on Selection**, and **0.626 on Selection-plus-Chain at nesting depth >= 3**. Independent dials beat a nested case table by a wide margin, which retroactively validates the spec's "two independent lookups, not a 9-cell case table" ruling.
- **There is no reliable precedence rule to lean on.** Anthropic states flatly that "if two rules contradict each other, Claude may pick one arbitrarily." IHEval ([arXiv:2502.08745](https://arxiv.org/abs/2502.08745)) measures a 21-65 point drop between aligned and conflicting variants of the same task, with the best open-source model at 48% on conflict resolution. OpenAI's GPT-4.1 guide is the one vendor statement of a positional rule ("tends to follow the one closer to the end of the prompt"), and OpenAI's own 2026 model-guidance page tells you not to rely on it: state each instruction once. **A rule written twice with different conditions is a coin flip, not an override.**
- **Everyone who can move the conditional out of prose does.** LangGraph, CrewAI Flows, AutoGen GraphFlow, Microsoft Agent Framework edges, and Google ADK workflow agents all put the branch in a callable or a typed edge, and all give the same reason in different words: "Use deterministic steps where you need reliability and predictability, and agentic steps where you need flexibility" (LangGraph). Cursor, GitHub Copilot, and AGENTS.md hoist activation conditions into frontmatter globs or file-tree position so the harness, not the model, evaluates them. **Anthropic's Agent Skills spec is the outlier: it offers no conditional metadata at all beyond free-text `description`,** which is exactly the regime forge is in - and is why the strongest published skill (`claude-api`) resolves its own skip condition with a `grep` rather than a judgment.
- **The mitigations that measurably work are external checks, not self-reports.** Deterministic pre-execution gates recover +12.4 points on tau-bench airline ([arXiv:2607.07405](https://arxiv.org/abs/2607.07405)); tool-verified refinement "doubles Llama3.1-8B's constraint adherence and triples Mistral-7B's" ([arXiv:2410.12207](https://arxiv.org/abs/2410.12207)); a state-machine harness beats prose control flow by 13-28 points at 3-5x lower cost ([arXiv:2403.11322](https://arxiv.org/abs/2403.11322)). Meanwhile "Models Recall What They Violate" ([arXiv:2604.28031](https://arxiv.org/abs/2604.28031)) `[2026 preprint]` finds 97.3% constraint recall alongside knows-but-violates rates up to 99% - **asking the orchestrator to restate the gate does not predict that it will honor the gate.** Emissions have to be checkable by something other than the emitter.

---

## 1. First-party guidance on conditional instructions

### 1.1 Anthropic

The only vendor that ships a named template for branching inside a Markdown instruction file.

**The template.** [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), section "Conditional workflow pattern", lead-in "Guide Claude through decision points:":

```markdown
1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: ...
3. Editing workflow: ...
```

Shape worth naming: a numbered **classify** step first, then a bolded question with an arrow to a named branch, then the branches as sibling top-level steps. Not nested `if/else`, not a decision tree.

**The escape hatch, same page:** "If workflows become large or complicated with many steps, consider pushing them into separate files and tell Claude to read the appropriate file based on the task at hand."

**The gate grammar, same page.** Anthropic's own feedback-loop examples give a usable syntax for a hard stage gate: `4. **Only proceed when validation passes**` as its own numbered step; `If validation fails:` with an indented remediation sub-list; and `If citations are incomplete, return to Step 3.` for the loop-back.

**Checklists as the anti-skip device, same page:** "Break complex operations into clear, sequential steps. For particularly complex workflows, provide a checklist that Claude can copy into its response and check off as it progresses," with the mechanism named: "Clear steps prevent Claude from skipping critical validation." Note the emission is the point - copied into the response, not merely present in the file.

**Calibrating which stages deserve a hard gate, same page:** "Match the level of specificity to the task's fragility and variability," with the robot analogy - "Narrow bridge with cliffs on both sides: There's only one safe way forward. Provide specific guardrails and exact instructions (low freedom)" vs "Open field with no hazards: Many paths lead to success."

**Do not enumerate every branch.** [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): "teams will often stuff a laundry list of edge cases into a prompt in an attempt to articulate every possible rule the LLM should follow for a particular task. We do not recommend this." Same page names the failure mode of over-branching directly: "engineers hardcoding complex, brittle logic in their prompts to elicit exact agentic behavior. This approach creates fragility and increases maintenance complexity over time," with the caption "brittle if-else hardcoded prompts" at one end of the altitude spectrum.

**The human-decidability test, same page:** "If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better." Stated about tools; applies verbatim to a band boundary.

**Length.** [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) states the same limit three times on one page: "Keep SKILL.md body under 500 lines for optimal performance"; "Split content into separate files when approaching this limit"; and as a shipping checkbox. [Claude Code skills docs](https://code.claude.com/docs/en/skills) repeat it. The token-denominated companion, from the [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) progressive-disclosure table: Level 1 metadata "~100 tokens per Skill", Level 2 instructions "Under 5k tokens", Level 3 bundled resources "None until accessed". CLAUDE.md is budgeted tighter: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence" ([memory docs](https://code.claude.com/docs/en/memory)).

**Nesting limit on the split remedy:** "Claude may partially read files when they're referenced from other referenced files... **Keep references one level deep from SKILL.md**." A branch body two hops from the entry file risks a truncated read - which for a gate means the condition may never be seen.

**Precedence: none.** [How Claude remembers your project](https://code.claude.com/docs/en/memory): "**Consistency**: if two rules contradict each other, Claude may pick one arbitrarily." Load order is broad-to-specific by concatenation, but the docs are explicit that this carries no semantic override. Same page sets the reliability ceiling on any Markdown gate: "CLAUDE.md content is delivered as a user message after the system prompt... Claude reads it and tries to follow it, but there's no guarantee of strict compliance, especially for vague or conflicting instructions."

**Restating a rule at the point of action.** [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5): "In a long system prompt, pair the instruction with a short reminder near the end of the prompt." This is the one first-party endorsement of controlled duplication, and it is scoped to *reminder*, not restatement of the rule's content.

**Emit before acting.** [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents): "we recommend instructing agents to output not just structured response blocks (for verification), but also reasoning and feedback blocks. Instructing agents to output these before tool call and response blocks may increase LLMs' effective intelligence by triggering chain-of-thought (CoT) behaviors."

**Literalism, and why scope must be written out.** [Prompting Claude Sonnet 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5): "It does not silently generalize an instruction from one item to another... If you need Claude to apply an instruction broadly, state the scope explicitly." And on qualitative bars: when a prompt says "only report high-severity issues... it may investigate the code just as thoroughly, identify the bugs, and then not report findings it judges to be below your stated bar," so "be concrete about where the bar is rather than using qualitative terms."

**Emphasis: an unresolved first-party conflict.** [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) says "You can tune instructions by adding emphasis (e.g., 'IMPORTANT' or 'YOU MUST') to improve adherence," and the Skills authoring page suggests escalating "always filter" to "MUST filter". The current model-specific guidance says the opposite: "If your prompts were designed to reduce undertriggering on tools or skills, these models may now overtrigger. The fix is to dial back any aggressive language," and calls out `"If in doubt, use [tool]"` by name as a cause of over-triggering. Anthropic's own `skill-creator` skill sides with the second: "If you find yourself writing ALWAYS or NEVER in all caps... that's a yellow flag."

**The hard ceiling.** [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices): "Unlike CLAUDE.md instructions which are advisory, hooks are deterministic and guarantee the action happens." And from the memory docs: "If the instruction is something that must run at a specific point, such as before every commit or after each file edit, write it as a hook instead."

**Observed practice.** The [published Claude Opus 5 system prompt](https://platform.claude.com/docs/en/release-notes/system-prompts) (dated 2026-07-24) encodes its own conditionals as plain third-person prose, no arrows or trees: "If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed with the request." It also carries a **state-carrying conditional** - "Once Claude refuses a request for reasons of child safety, all subsequent requests in the same conversation must be approached with extreme caution" - which is structurally a mode change on a gate, forge's ratchet in miniature. Rules are grouped under one snake_case XML block (`<critical_child_safety_instructions>`).

### 1.2 OpenAI

**Contradictions have a named, quantified cost.** [GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide), section "Instruction following":

> "GPT-5 follows prompt instructions with surgical precision... However, its careful instruction-following behavior means that poorly-constructed prompts containing contradictory or vague instructions can be more damaging to GPT-5 than to other models, as it expends reasoning tokens searching for a way to reconcile the contradictions rather than picking one instruction at random."

**And a worked fix that is directly the shape forge needs.** The guide's healthcare example has a rule "Always look up the patient profile before taking any other actions" colliding with an emergency-escalation rule. OpenAI's recommended repair is **not** a precedence declaration; it is rewriting the rule so the exception lives inside it: "Do not do lookup in the emergency case, proceed immediately to providing 911 guidance." Conclusion: "By resolving the instruction hierarchy conflicts, GPT-5 elicits much more efficient and performant reasoning."

Generalized in the [GPT-5.1 guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide): "Make tradeoffs explicit (for example, clearly state when to prioritize concision over completeness, or exactly when tools must vs must not be called)" and "Prefer small, explicit edits: clarify conflicting rules, remove redundant or contradictory lines."

**One home per rule.** [Model guidance](https://developers.openai.com/api/docs/guides/prompt-guidance): "Keep the policy in one place and state each instruction once. Repeating instructions such as 'ask first,' 'do not mutate,' or 'wait for approval' can cause unnecessary approval requests for safe, expected actions." Note the named cost of duplication is over-firing.

**The one positional precedence statement.** [GPT-4.1 prompting guide](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide): "If there are conflicting instructions, GPT-4.1 tends to follow the one closer to the end of the prompt." Formalized in the [Model Spec](https://model-spec.openai.com/2025-10-27.html) chain of command: a candidate instruction is not applicable if it is "superseded by an instruction in a later message at the same level," and "When two root-level principles conflict, the model should default to inaction."

**Branch count as a scaling smell.** [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf), p.16:

> "**Complex logic** - When prompts contain many conditional statements (multiple if-then-else branches), and prompt templates get difficult to scale, consider dividing each logical segment across separate agents."

Counterweight on p.11, which explicitly endorses prose branching for the edge-case tier: "A robust routine anticipates common variations and includes instructions on how to handle them with conditional steps or branches such as an alternative step if a required piece of info is missing." Read together: branch in prose within a routine; split when branch count makes the template unscalable. Their canonical instruction format is "a clear set of instructions, written in a numbered list" with "no ambiguity" as the acceptance criterion (p.12).

**Format.** The [GPT-4.1 guide](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide) is the only first-party head-to-head: Markdown - "We recommend starting here, and using markdown titles for major sections and subsections"; XML - "performed well in our long context testing"; JSON - "performed particularly poorly". The GPT-5 guide adds that "structured XML specs like `<[instruction]_spec>` improved instruction adherence on their prompts and allows them to clearly reference previous categories." The [GPT-5.2 guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) gives the only criterion anyone states for tables: "Use tables when the reader's job is to compare or choose among options."

**Placement in long context.** GPT-4.1 guide: "place your instructions at both the beginning and end of the provided context... If you'd prefer to only have your instructions once, then above the provided context works better than below." This sits in unresolved tension with the "state each instruction once" guidance above; the regimes differ (long-context Q&A vs agent policy).

### 1.3 Google

**Instructions over constraints, with the clash mechanism named.** Prompt Engineering whitepaper (Lee Boonstra, distributed via Kaggle; read through an [Internet Archive full-text mirror](https://archive.org/stream/whitepaper-prompt-engineering-v-4/whitepaper_Prompt%20Engineering_v4_djvu.txt) `[mirror of the primary PDF, not a google.com fetch]`):

> "Instructions directly communicate the desired outcome, whereas constraints might leave the model guessing about what is allowed."
> "**Also a list of constraints can clash with each other.**"
> "As a best practice, start by prioritizing instructions, clearly stating what you want the model to do and only use constraints when necessary for safety, clarity or specific requirements."

Verified absence, checked twice: the whitepaper contains **no** section on conditional or branching instructions, if-then logic, or rule precedence.

**Decomposition is Google's answer to complexity.** [Prompt design strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies): "Break down instructions: Instead of having many instructions in one prompt, create one prompt per instruction" and "Chain prompts: For complex tasks that involve multiple sequential steps, make each step a prompt and chain the prompts together." Structurally the same move as OpenAI's split-into-agents.

**Placement: instructions last, unconditionally.** Same page: "When providing large amounts of context (e.g., documents, code), supply all the context first. Place your specific instructions or questions at the very *end* of the prompt." Reinforced in the [long context doc](https://ai.google.dev/gemini-api/docs/long-context) and the [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3). This is the sharpest cross-vendor disagreement in the survey: OpenAI says top-and-bottom, and if only once, top.

**Anti-verbosity for prompts themselves.** [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3): "Be concise in your input prompts. Gemini 3 responds best to direct, clear instructions. It may over-analyze verbose or overly complex prompt engineering techniques used for older models."

`[unverified]` The Gemini 3 prompting guide on Google Cloud reportedly warns that for sufficiently complex requests the model may drop negative or formatting constraints appearing too early, recommending critical restrictions as the final line. All `docs.cloud.google.com` and `cloud.google.com/vertex-ai` prompt pages render client-side and returned only navigation chrome across repeated fetches; treat as unconfirmed.

### 1.4 Where the vendors agree and disagree

| Topic | Anthropic | OpenAI | Google |
| --- | --- | --- | --- |
| Conditionals in prose | Named template ("Conditional workflow pattern") | Endorsed for edge cases within a routine | No guidance found |
| When to stop branching in prose | "push them into separate files" | "divide each logical segment across separate agents" | "one prompt per instruction" |
| Contradictory rules | "may pick one arbitrarily" | Costs reasoning tokens; fix by rewriting the rule | "a list of constraints can clash with each other" |
| Precedence rule | None documented | Later-in-prompt wins (GPT-4.1); Model Spec chain of command | None documented |
| Repeating a rule | Short reminder near the end of a long prompt | "state each instruction once" (agent policy); top-and-bottom (long context) | Not addressed |
| Instruction position vs bulk context | Data at top, query at end (up to 30% quality gain claimed) | Both ends; if once, top | End, unconditionally |
| Format | Markdown headers or XML tags; no ruling on tables | Markdown default, XML good, JSON poor; tables for comparison/choice | Structure endorsed; JSON for output |
| Affirmative phrasing | "Tell Claude what to do instead of what not to do" | Implicit | "Use Instructions over Constraints" |
| File length | 500 lines / under 5k tokens (SKILL.md); 200 lines (CLAUDE.md) | No prompt-length guidance found | "Be concise in your input prompts" |

Three genuine agreements: contradictory rules are a first-class defect with a real cost; proliferating conditionals in one file is a structural smell with a structural fix; affirmative phrasing beats prohibitions. One genuine disagreement: where instructions go relative to bulk context.

---

## 2. How published instruction artifacts actually encode conditional gating

Read at the file level from `anthropics/skills` (HEAD `b29e7cf65e5c`, committed 2026-07-24), `anthropics/claude-code`, and `github/docs@main`.

### 2.1 `anthropics/skills` - the real distribution

Measured `wc -l` on every shipped `SKILL.md`: `internal-comms` 32, `frontend-design` 55, `theme-factory` 59, `brand-guidelines` 73, `web-artifacts-builder` 73, `docx` 91, `webapp-testing` 95, `xlsx` 99, `canvas-design` 129, `mcp-builder` 236, `pptx` 238, `slack-gif-creator` 254, `pdf` 314, `doc-coauthoring` 375, `algorithmic-art` 404, `skill-creator` 485, `claude-api` 546. Bimodal: production document skills at 73-314 lines, workflow/meta skills at 375-546. `claude-api` exceeds Anthropic's own published 500-line guidance.

**Pattern A - table-first dispatch.** The three highest-traffic skills put a routing table in the first 15 lines, before any prose. `docx/SKILL.md`:

```
A `.docx` is a ZIP archive of XML files. Choose your approach by task:

| Task | Approach |
|---|---|
| **Create** a new document | Write a `docx` (npm) script - see gotchas below |
| **Edit** an existing document | `unzip` → edit `word/document.xml` → `zip` |
| **Read** content | `pandoc -t markdown file.docx` |
```

`pptx` uses the identical shape; `xlsx` drops the lead-in and opens with the bare table. The body is then a flat pile of per-branch detail with no branch announcement.

**Pattern B - inline bolded `If X` clause.** The gate is a bolded sentence-initial fragment inside an otherwise flat bullet list, carrying its own justification. `pptx/SKILL.md`: "**If the deck came from a template, always pass `--original`.** A template may itself contain parts the XSD rejects, so a bare run can report failures you never caused."

**Pattern C - drawn decision tree.** Exactly one instance in the whole repo (`webapp-testing/SKILL.md`, an ASCII tree with `├─`/`└─` branches). Rarity is the finding.

**Pattern D - the condition hoisted into frontmatter.** `claude-api/SKILL.md` puts a TRIGGER/SKIP pair inside the YAML `description`, with an explicit precedence declaration and a delegated deterministic check:

> "TRIGGER - read BEFORE opening the target file; don't skip because it 'looks like a one-liner' - whenever: ..."
> "SKIP only when another provider is being worked on (**overrides all triggers**): OpenAI/GPT/Gemini/... named in the query; OR `grep -rE 'openai|langchain_openai|...'` over the project hits (**run this grep FIRST if no provider named** - don't Read the file)."

Three things: the skip precedence is stated explicitly rather than left to position; the condition is partly delegated to `grep` so the model runs a check instead of forming a judgment; and the check is ordered before the expensive step.

**Pattern E - a fixed conditional slot label.** The strongest scannable convention found anywhere: `plugins/claude-opus-4-5-migration/skills/.../SKILL.md` turns off a whole half of the skill by default - "**Only apply these fixes if the user explicitly requests them or reports a specific issue.** By default, just update model strings" - then re-enables each item with an identical one-line predicate, five times:

> `**Apply if**: User reports tools being called too frequently or unnecessarily.`
> `**Apply if**: User reports unwanted files, excessive abstraction, or unrequested features.`
> `**Apply if**: User reports the model proposing fixes without inspecting relevant code.`

A fixed label the reader scans for, rather than prose that varies per section.

**Pattern F - the deterministic gate.** Where a predicate can be made mechanical, the best artifacts make it so. `pptx/SKILL.md` ends its QA section with a shell command and then: "If grep returns results, fix them before declaring success."

**Load-bearing gates get repeated.** `pdf/SKILL.md` states its FORMS.md gate three separate times in 314 lines (Overview paragraph, Quick Reference table row, Next Steps list). The Opus 4.5 migration skill states "does not migrate Haiku" once in the description and once in the body.

**Structured emission before branching is essentially absent.** No skill in the repo requires the model to declare which path it is taking before executing it. The closest analogues are `doc-coauthoring`'s nine `Announce ...` stage markers (stage transitions, not branch selection) and `frontend-design`'s "pin it yourself before designing... and state your choice."

**ALL-CAPS emphasis is concentrated in the creative skills, not the production ones.** `docx`, `xlsx`, `internal-comms`, `brand-guidelines`, `mcp-builder`, `slack-gif-creator`, and `doc-coauthoring` contain **zero** MUST/NEVER/ALWAYS/IMPORTANT/CRITICAL tokens. `canvas-design` (129 lines) has 10, `algorithmic-art` has 14.

### 2.2 Anthropic's authoring doctrine, as shipped

`skill-creator/SKILL.md` argues against hard conditionals and against emphasis, twice: "Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs," and "If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag - if possible, reframe and explain the reasoning so that the model understands why the thing you're asking for is important." It also states the branch-by-directory pattern (`references/aws.md`, `gcp.md`, `azure.md`, with "Claude reads only the relevant reference file") and the triggering rule: "All 'when to use' info goes here, not in the body."

The formal spec at [agentskills.io/specification](https://agentskills.io/specification) has moved out of the repo. It confirms the three-level budget ("Metadata (~100 tokens)", "Instructions (< 5000 tokens recommended)", "Resources (as needed)"), the 500-line cap, and the one-level-deep reference rule. Frontmatter fields are `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. **There is no glob field, no `applyTo`, no `alwaysApply`** - which is precisely why `claude-api` has to stuff a TRIGGER/SKIP block into free text.

### 2.3 Claude Code plugin commands

`plugins/code-review/commands/code-review.md` (109 lines) is the strongest hard gate in any official artifact, and it does two notable things. It **delegates the gate evaluation to a cheap subagent**:

> "1. Launch a haiku agent to check if any of the following are true: [4 conditions] ... If any condition is true, stop and do not proceed."

And where the condition can be a literal rather than a judgment, it is - a three-way branch on a CLI flag:

> "If `--comment` argument was NOT provided, stop here... If `--comment` argument IS provided and NO issues were found, post a summary comment... and stop. If `--comment` argument IS provided and issues were found, continue to step 8."

Contrast `plugins/feature-dev/commands/feature-dev.md`, which has no real conditions and therefore falls back on emphasis: "**CRITICAL**: This is one of the most important phases. DO NOT SKIP." The gating command uses `if ... stop`; the linear one uses caps.

### 2.4 Cursor rules - condition as frontmatter

[cursor.com/docs/context/rules](https://cursor.com/docs/context/rules). Four declarative activation types: `Always Apply` ("Apply to every chat session"), `Apply Intelligently` ("When Agent decides it's relevant based on description"), `Apply to Specific Files` ("When file matches a specified pattern"), `Apply Manually` ("When @-mentioned in chat"). `[unverified]` The older widely-cited labels (Always / Auto Attached / Agent Requested / Manual) could not be confirmed on the live page; the page is JS-rendered with no raw-markdown endpoint, and `globs` did not appear in the frontmatter example returned.

Confirmed verbatim: "**Keep rules under 500 lines**", "Split large rules into multiple, composable rules", "Avoid vague guidance. Write rules like clear internal docs", and "Reference files instead of copying their contents - this keeps rules short and prevents them from becoming stale as code changes."

The architectural point: Cursor gives the author a four-way choice about **who evaluates the condition** - nobody (always), the harness (glob), the model (description), or the user (@-mention). The rule body never has to carry "run this only when...". The 500-line number matching Anthropic's exactly is two independent vendors converging.

### 2.5 GitHub Copilot - `applyTo` globs, and a stated rationale

From `github/docs@main` source markdown. Three instruction types: repository-wide `copilot-instructions.md`, path-specific `*.instructions.md`, and agent instructions (`AGENTS.md`/`CLAUDE.md`/`GEMINI.md`). The rationale for hoisting the condition is stated plainly:

> "By using path-specific instructions you can avoid overloading your repository-wide instructions with information that only applies to files of certain types, or in certain directories."

Mechanism: `applyTo: "**/*.ts,**/*.tsx"` in frontmatter, plus a second metadata axis nobody else exposes - `excludeAgent: "code-review"` gates which agent reads the file at all.

**Precedence is declared but advisory.** The docs give a full ordering (Personal > Path-specific > Repository-wide > Agent > Organization) and then undercut it: "However, all sets of relevant instructions are provided to Copilot." The conflict guidance is one sentence: "Whenever possible, try to avoid providing conflicting sets of instructions."

**GitHub publishes a list of instruction shapes that do not work at scale** - and the first entry is a conditional-reference failure, i.e. the progressive-disclosure move Anthropic's skills depend on:

> "The following types of instructions may work for a small repository with only a few contributors, but for a large and diverse repository, **these may cause problems**: Requests to refer to external resources when formulating a response; Instructions to answer in a particular style; Requests to always respond with a certain level of detail"

**A real artifact worth copying.** `github/docs`'s own `.github/instructions/instruction-architecture.instructions.md` is 13 lines and layers three gate mechanisms: an `applyTo` glob narrows the file set deterministically; prose narrows further inside that set ("It does **not** apply to code instructions or agents owned by the engineering team") because globs cannot express ownership; and the gated stage is a mandatory external read with an explicit failure branch - "If you cannot access it, say so and stop rather than guessing."

### 2.6 AGENTS.md - condition as file-tree position

[agents.md](https://agents.md). The format has **no metadata at all**: no frontmatter, no glob, no description. Its entire conditional expressiveness is directory placement. "Agents automatically read the nearest file in the directory tree, so the closest one takes precedence." FAQ: "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything." OctoBench ([arXiv:2601.10343](https://arxiv.org/abs/2601.10343)), which benchmarks exactly this - scaffold-specified instructions in repository-grounded agentic coding across 34 environments and 217 tasks - reports "a systematic gap between task-solving and scaffold-aware compliance," i.e. models solve the task while failing the repo's rules.

---

## 3. Prose vs code: where every framework puts the branch

Three mechanisms recur: **(a)** a callable or typed edge the runtime evaluates, **(b)** a tool call the model must emit, **(c)** free prose the model interprets.

### 3.1 LangGraph - (a) callable, with the branch set declarable

`add_conditional_edges(source, path, path_map)` takes "The callable that determines the next node or nodes." The [API reference](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges) carries the analyzability warning: "Without type hints on the `path` function's return value (e.g., `-> Literal[\"foo\", \"__end__\"]:`) or a path_map, the graph visualization assumes the edge could transition to any node in the graph." `Command` requires the same declaration at type level: "you must add return type annotations with the list of node names the node is routing to."

The rationale sentence, from the [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), verified by direct re-fetch:

> "Use deterministic steps where you need reliability and predictability, and agentic steps where you need flexibility"

Their [workflows-and-agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) page splits the space: "Workflows have predetermined code paths and are designed to operate in a certain order" vs "Agents are dynamic and define their own processes." Their own Router pattern uses an LLM with a **structured-output schema** to pick a label, then a conditional edge acts on it - the model classifies, the runtime branches.

### 3.2 CrewAI - (a) callable over typed output, plus a decision guide

`ConditionalTask` takes a Python predicate over the previous task's structured output (`output.pydantic.events`), with the polarity in a code comment: "If false, the task will be skipped, if true, then execute the task" ([Conditional Tasks](https://docs.crewai.com/en/learn/conditional-tasks)). `@router` returns a string label that `@listen("<label>")` methods subscribe to.

The [Crews-vs-Flows decision guide](https://docs.crewai.com/en/guides/concepts/evaluating-use-cases) frames the axis as complexity vs precision and lists, as reason #4 to choose Flows: "**The workflow involves conditional logic** - Different paths need to be taken based on intermediate results." CrewAI's own guidance is that branching is a reason to leave the autonomous layer.

Negative finding worth recording: the [hierarchical process](https://docs.crewai.com/en/concepts/processes) page, where routing *is* delegated to a manager LLM, carries **no reliability caveat at all**.

### 3.3 AutoGen and Microsoft Agent Framework - all three mechanisms, with a documented ladder

AutoGen's `SelectorGroupChat` is mechanism (c) in its purest form. The library default `selector_prompt` (read from `_selector_group_chat.py` on `main`) is a role-play prompt:

```
You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to play. Only return the role.
```

And the [docs](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html) give the escalation rule, verified by direct re-fetch:

> "Generally, if you find yourself writing multiple conditions for each agent, it is a sign that you should consider using a custom selection function, or breaking down the task into smaller, sequential tasks to be handled by separate agents or teams."

Plus: "Try not to overload the model with too much instruction in the selector prompt."

`GraphFlow` is mechanism (a) - `condition=lambda msg: "APPROVE" not in msg.to_model_text()` on a `DiGraph` edge - with the trigger to climb the ladder stated: "Transition to a structured workflow when your task requires deterministic control, conditional branching, or handling complex multi-step processes with cycles."

[Microsoft Agent Framework Workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/) states the agent/workflow split: "The steps an agent takes are dynamic and determined by the LLM" vs "The flow of a workflow is explicitly defined, allowing for more control over the execution path." Their [edges doc](https://learn.microsoft.com/en-us/agent-framework/workflows/edges) supplies the defensive vocabulary a prose gate lacks: "**Defensive Routing**: Condition functions handle edge cases to prevent workflow dead-ends"; switch-case "**Guaranteed Routing**: The `WithDefault()` method ensures messages never get stuck"; and in the sample code, the comment "Fail closed on parse errors so we do not accidentally route to the wrong path."

**The single best documented failure mode of a model-emitted branch** is Microsoft's handoff caveat:

> "because handoffs are achieved through tool calls, if an agent does not call a handoff tool but generates a response instead, **the workflow won't know what to do next but to delegate back to the user for further input**. It is also **not possible to force an agent to always handoff** by requiring it to call the handoff tool, because the agent won't be able to generate meaningful responses otherwise."

An optional emission cannot be forced. Their fallback for silence is a canned continuation prompt.

### 3.4 OpenAI Agents SDK, Semantic Kernel, Google ADK

OpenAI Agents SDK is mechanism (b): "Handoffs are represented as tools to the LLM. So if there's a handoff to an agent named `Refund Agent`, the tool would be called `transfer_to_refund_agent`" ([handoffs](https://openai.github.io/openai-agents-python/handoffs/)). Notably, even with a structured channel available, the SDK ships a prose `RECOMMENDED_PROMPT_PREFIX` to make the model reach for it. Their [orchestration page](https://openai.github.io/openai-agents-python/multi_agent/): "Orchestrating via LLM is powerful, orchestrating via code makes tasks more deterministic and predictable."

Semantic Kernel's handoff is a hybrid worth naming: the allowed edges are declared in code, but *which* allowed edge fires is decided by the model reading a prose `description` string ("Transfer to this agent if the issue is not refund related").

Google ADK names a **three-way** taxonomy where most discussions have two. [Agent routing](https://adk.dev/agents/routing/): "`RoutedAgent` is different from workflow agents like `SequentialAgent` or `ParallelAgent`, which orchestrate multiple agents in a fixed pattern, and from LLM-driven delegation, where the LLM decides which agent to hand off to. With `RoutedAgent`, you write an explicit routing function that selects one agent per invocation." The determinism claim is on [workflow agents](https://adk.dev/workflows/): they determine sequence "without consulting an AI model for assistance with the orchestration... This approach results in deterministic and predictable execution patterns."

### 3.5 The pattern

| System | Conditional lives in | Stated rationale |
| --- | --- | --- |
| LangGraph `add_conditional_edges` / `Command` | (a) Python callable, branch set type-declarable | "deterministic steps where you need reliability and predictability" |
| CrewAI `ConditionalTask` / `@router` | (a) Python predicate over typed output | conditional logic is a stated reason to leave the autonomous layer |
| CrewAI hierarchical process | (c) LLM manager | no caveat documented |
| AutoGen `SelectorGroupChat` | (c) free prose (role-play prompt) | climb out "if you find yourself writing multiple conditions for each agent" |
| AutoGen `Swarm` / OpenAI Agents SDK handoffs | (b) tool call | parallel tool calling "can lead to unexpected behavior" |
| AutoGen `GraphFlow` / MS Agent Framework edges | (a) predicate over validated message | "fail closed"; `WithDefault()` "ensures messages never get stuck" |
| MS Agent Framework handoff | (b) injected handoff tool | "not possible to force an agent to always handoff" |
| Google ADK workflow agents / `RoutedAgent` | (a) fixed pattern, or an explicit routing function | "without consulting an AI model for assistance with the orchestration" |
| Cursor `Apply to Specific Files`, Copilot `applyTo`, AGENTS.md | metadata/file-tree, harness-evaluated | "avoid overloading your repository-wide instructions" (GitHub) |
| **Anthropic Agent Skills** | **(c) prose only - the spec offers no conditional metadata** | context economy, not reliability |

Two independent frameworks name **branching complexity itself** as the trigger to move the conditional out of the prompt (AutoGen, CrewAI), matching the three vendors in §1.4. forge sits in the one cell with no metadata escape hatch, which makes the prose-side discipline load-bearing rather than optional.

---

## 4. Measured instruction-following degradation

### 4.1 Conditional composition specifically

**ComplexBench** ([arXiv:2407.03978](https://arxiv.org/abs/2407.03978), NeurIPS 2024 D&B; definitions and Table 5 read from the PDF). 1,150 instructions, 5,306 scoring questions, 4 constraint types x 19 dimensions x 4 composition types. The composition definitions, verbatim:

> "**And**. The output needs to satisfy multiple constraints simultaneously."
> "**Chain**. The output is required to complete multiple tasks in the instruction sequentially."
> "**Selection**. The output is required to select different branches according to certain conditions, fulfilling the constraints of the corresponding branch."

DRFR by composition type, GPT-4-1106: **And 0.881 | Chain avg 0.766 | Selection avg 0.765 (depth 1: 0.815, depth 2: 0.772, depth >= 3: 0.694) | Selection-and-Chain avg 0.675 (depth >= 3: 0.626) | overall 0.800**. The paper: "as the complexity of composition types within instruction increases, the performance of all LLMs significantly drops, especially on Selection and Chain."

Two secondary findings that matter here. First, decomposing an instruction into multi-round interaction made things **worse**, not better (GPT-3.5-Turbo overall 0.682 → 0.652; Selection-and-Chain depth >= 3, 0.482 → 0.415), attributed to "cumulative errors in multi-round interactions." Second, the authors had to expand selection branches to counter a bias: "in all the selection compositions with two branches, annotators have about a 70% probability of selecting the first branch as the correct one," and they note a model "predisposition toward random selection."

**AgentIF** ([arXiv:2505.16944](https://arxiv.org/abs/2505.16944)). 707 real agentic instructions, average 1,723 words and 11.9 constraints. Constraint presentation types include "**Condition constraints**: triggered only under specific conditions, which may be derived from the input... or from the model's own output behavior." Best model o1-mini reaches **CSR 59.8 / ISR 27.2**. Condition constraints score 15-26 points below vanilla constraints on the same models (o1-mini 80.8 → 66.1; GPT-4o 80.8 → 65.8; DeepSeek-R1 87.0 → 61.4). The error decomposition is the headline:

> "two main types of failure... incorrect condition checking, where the LLM fails to determine whether a condition is triggered; and instruction following failure, where the LLM fails to follow the constraint even when the condition is triggered."
> "a substantial portion (above 30%) of errors are due to incorrect condition checks"

And on length: "when instruction length exceeds 6,000 words, the ISR scores of all models are nearly 0."

**RealGuardrails** ([arXiv:2502.12197](https://arxiv.org/abs/2502.12197)) is the closest analog in the literature to a stage-gated pipeline file, and its numbers are the ones this survey leans on hardest, so they were read off the PDF. Its "Monkey Island" stress test inserts G guardrails - conditional behaviors "under particular conditions, which we can trigger with pre-specified user messages" - into one system message and scales G from 1 to 20. Verbatim:

> "Figure 2. Model performance quickly approaches zero when stress tested with an increasing number of guardrails in the system message."
> "even though models can follow a few guardrails reasonably well, the performance of recent LLMs uniformly approaches zero as the number of guardrails increases. **This stress test does not involve conflicting instructions, adversarial inputs, tool-calling, or long context windows, all factors that further increase the difficulty of following the system prompt.**"
> "Real-world system prompts often contain as many or even more guardrails. Among the GPT Store and HuggingChat prompts used in our experiments, we found an average of **5.1 guardrails per prompt**."

Their hypothesis for the mechanism, stated when the same effect reappears on banned-word lists: "Adding too many guardrails to a system prompt seems to overwhelm the model's 'working memory'." The abstract's framing is the failure mode in one clause: "models often forget to consider relevant guardrails or fail to resolve conflicting demands between the system and the user."

### 4.2 Constraint count is the dominant variable

- **IFScale** ([arXiv:2507.11538](https://arxiv.org/abs/2507.11538)): 500 instructions on one task, 20 models. "even the best frontier models only achieve 68% accuracy at the max density of 500 instructions," with "3 distinct performance degradation patterns, bias towards earlier instructions, and distinct categories of instruction-following errors." Crucially: "Models overwhelmingly err toward **omission** errors as instruction density increases" - the silent-skip mode, quantified (llama-4-scout omission:modification ratio 34.9 at 500).
- **ManyIFEval** ([arXiv:2509.21051](https://arxiv.org/abs/2509.21051)): "performance consistently degrades as the number of instructions increases," and a logistic regression on instruction count alone predicts performance to about 10% error.
- **FollowBench** ([arXiv:2310.20410](https://arxiv.org/abs/2310.20410)) adds exactly one constraint per difficulty level across five constraint types. `[html]` GPT-4-1106 hard satisfaction rate by level 84.7 → 75.6 → 70.8 → 73.9 → 61.9, with GPT-4 and GPT-3.5 consecutively satisfying around three constraints on average. Figures are HTML-derived and not PDF-confirmed; the shape (monotonic decline per added constraint) is the transferable part.
- **CFBench** ([arXiv:2408.01122](https://arxiv.org/abs/2408.01122)): GPT-4o full set CSR 0.886 but ISR 0.653 - the per-constraint to per-instruction collapse is the constraint-count effect in one number.
- **IFEval** ([arXiv:2311.07911](https://arxiv.org/abs/2311.07911)), the baseline: GPT-4 prompt-level strict 76.89% vs instruction-level strict 83.57%. Partial compliance is the norm even at 25 verifiable instruction types.

### 4.3 Multi-turn and long-context drift

- **LLMs Get Lost In Multi-Turn Conversation** ([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)): "an average drop of 39% across six generation tasks," 200,000+ simulated conversations, 15 LLMs. The decomposition: "Model aptitude degrades in a non-significant way... with an average drop of 16%. On the other hand, unreliability skyrockets with an average increase of 112%... all models we test exhibit very high unreliability, with performance degrading 50 percent points on average between the best and worst simulated run for a fixed instruction." Named cause (1): "LLMs prematurely propose full answer attempts, making assumptions about problem specifications." A CONCAT control retaining 95.1% of full performance rules out information loss - the damage is from turn structure. Two turns is enough; temperature 0 does not fix it; reasoning models do not fix it.
- **Multi-IF** ([arXiv:2410.15553](https://arxiv.org/abs/2410.15553)), Table 1 read from PDF: GPT-4o 0.843 → 0.724 → 0.631 across three turns; o1-preview 0.877 → 0.783 → 0.707; Claude-3.5-Sonnet 0.817 → 0.705 → 0.634. "LLMs increasingly forget to adhere to instructions that were successfully executed in previous turns."
- **SysBench** ([arXiv:2408.10943](https://arxiv.org/abs/2408.10943)) targets system-message instructions specifically - the closest benchmark analogue to a doctrine file - with three failure axes: "constraint violation, instruction misjudgement and multi-turn instability." Tables read from PDF: GPT-4o overall CSR 87.1 / ISR 76.4 / session success 54.4; on dependent conversations, per-turn instruction success falls 84.8% at turn 1 to 33.7% at turn 5, a regression slope of roughly 12.8 points per turn. Alignment matters: GPT-4o ISR 77.8% when system and user align, 71.4% when they do not. **And a chunk of the decay is self-inflicted**: replacing the model's own conversation history with ground-truth history recovers +4 to +10 ISR points at turns 2-5, i.e. later turns are partly poisoned by the model's own earlier bad turns rather than by length alone.
- **Instruction (In)Stability in Language Model Dialogs** ([arXiv:2402.10962](https://arxiv.org/abs/2402.10962), COLM 2024): "significant instruction drift within eight rounds of conversations," attributed to "attention decay over long exchanges."
- **LIFBench** ([arXiv:2411.07037](https://arxiv.org/abs/2411.07037)) is the long-context benchmark that targets instruction-following rather than retrieval, rubric-scored across 2,766 instructions and 20 models: "the performance of most models declines significantly as input length increases, particularly beyond 16k or 32k tokens." Best overall is GPT-4o at 0.758. Notably, format-shaped instructions hold up ("'Format' performance remains relatively stable across all input lengths in most models") while recognition-shaped ones fall fastest.
- **NoLiMa** ([arXiv:2502.05167](https://arxiv.org/abs/2502.05167)) on effective vs claimed context: "At 32K, for instance, 11 models drop below 50% of their strong short-length baselines. Even GPT-4o... experiences a reduction from an almost-perfect baseline of 99.3% to 69.7%." `[html]` Effective context (>= 85% of base) reported at 8K for GPT-4o against a 128K claim and 4K for Claude 3.5 Sonnet against 200K.
- **Same Task, More Tokens** ([arXiv:2402.14848](https://arxiv.org/abs/2402.14848)) isolates the cause cleanly - identical task, only padding varies - with average accuracy 0.92 → 0.68 going from ~250 to 3,000 tokens.

### 4.4 Position within the instruction set

- **Lost in the Middle** ([arXiv:2307.03172](https://arxiv.org/abs/2307.03172)): the U-shaped curve, with GPT-3.5-Turbo at 20 documents scoring roughly 75.8 first / 53.8 middle / 63.2 last against a 56.1 closed-book baseline - mid-context is worse than supplying nothing. But the same paper's query-aware ablation is the important nuance: repeating the query before *and* after takes key-value retrieval from 45.6% to 100%, yet "minimally affects performance trends in the multi-document question answering task." **Repetition is huge for retrieval-shaped tasks and roughly null for reasoning-shaped ones.**
- **Found in the Middle** ([arXiv:2406.16008](https://arxiv.org/abs/2406.16008)): "LLMs exhibit a U-shaped attention bias where the tokens at the beginning and at the end of its input receive higher attention, regardless of their relevance."
- **Direction is not portable.** IFScale finds primacy across all 20 models. MOSAIC ([arXiv:2601.18554](https://arxiv.org/abs/2601.18554)) `[2026 preprint]` finds primacy for Llama/Qwen3/DeepSeek but recency for Mixtral/Gemini/Claude, with a compliance cliff above 15 constraints. SIFo ([arXiv:2406.19999](https://arxiv.org/abs/2406.19999)) finds "a monotonic decline in performance as the position of an instruction in a sequence increases." Do not design a pipeline file around "the last rule wins."

### 4.5 Format

- **Does Prompt Formatting Have Any Impact on LLM Performance?** ([arXiv:2411.10541](https://arxiv.org/abs/2411.10541)): "GPT-3.5-turbo's performance varies by up to 40% in a code translation task depending on the prompt template, while larger models like GPT-4 are more robust." Preference is model-specific and flips: GPT-3.5 favors JSON, GPT-4 favors Markdown (73.9 JSON vs 81.2 Markdown on MMLU).
- **FormatSpread** ([arXiv:2310.11324](https://arxiv.org/abs/2310.11324)): "performance differences of up to 76 accuracy points when evaluated using LLaMA-2-13B" across semantically equivalent formats.
- **Let Me Speak Freely?** ([arXiv:2408.02442](https://arxiv.org/abs/2408.02442), Table 1 read from PDF). The common retelling is wrong: the damage comes from the **rigid schema, not the structure**. Claude-3-Haiku on GSM8K is unharmed by plain JSON (86.51 text → 86.99 JSON) and collapses only under an imposed schema (**23.44**). Mechanism, verbatim: "100% of GPT 3.5 Turbo JSON-mode responses placed the 'answer' key before the 'reason' key, resulting in zero-shot direct answering instead of zero-shot chain-of-thought reasoning." Parsing errors are not the cause. The inverse holds too: "in classification task JSON-mode performs much better than text due to the restriction on answer space."
- **Prompt Design at Scale** ([arXiv:2607.19257](https://arxiv.org/abs/2607.19257)) `[4-day-old single-author preprint, suggestive only]` runs the grid: "Perfect-response rate collapses to zero by N=80 for every model, every format, and both placements, a floor effect essentially independent of format." Instruction count dominates format and placement.

**Reading for a routing table:** the table-vs-bullets question has no strong evidence either way, and both Anthropic and OpenAI decline to rule on it in general. The one criterion anyone offers is OpenAI's: tables when the reader's job is to compare or choose among options. A dial lookup is exactly that. What the evidence *does* warn against is imposing a rigid emission schema that forces the decision before the reasoning.

### 4.6 Conflicting rules and precedence

- **IHEval** ([arXiv:2502.08745](https://arxiv.org/abs/2502.08745)): 3,538 examples across nine tasks, each in aligned and conflicting variants - a clean within-task delta. Abstract, verbatim: "All evaluated models experience a sharp performance decline when facing conflicting instructions, compared to their original instruction-following performance. Moreover, the most competitive open-source model only achieves **48% accuracy** in resolving such conflicts." `[html]` Per-model aligned-to-conflict drops of GPT-4o 91.0 → 70.0, Qwen-2 72B 85.7 → 47.8, LLaMA-3.1 70B 78.8 → 14.0, and a per-scenario split where GPT-4o handles safety conflicts at 94.0 but plain rule conflicts at 50.3 - the priority skill looks narrow rather than general.
- **The Instruction Hierarchy** ([arXiv:2404.13208](https://arxiv.org/abs/2404.13208), OpenAI) is the training-side answer, reporting robustness gains "up to 63%" - with over-refusal regressions as the cost.
- **Where Instruction Hierarchy Breaks** ([arXiv:2606.07808](https://arxiv.org/abs/2606.07808)) `[2026 preprint]` gives a three-way taxonomy - instruction identification, conflict resolution, response realization - and the distance finding: "increasing the distance between conflicting instructions generally increases IH non-compliance across models," with the failure *type* shifting from wrong-precedence to rule-never-noticed as distance grows.

---

## 5. Failure modes for LLM-executed conditionals

Naming note: "silent skip", "over-firing", "condition conflation", and "precedence error" are not established terms in this literature. The closest published taxonomy is ToolFailBench's four-way labelling (Tool-Skip / Result-Ignore / Output-Fabrication / Unnecessary-Tool-Use), and AgentIF's two-way split of condition errors. The mapping below is this survey's, and each mode is anchored to a measurement that exists rather than to the label.

### 5.1 Silent skip - the condition is never evaluated

The best-measured mode. **ToolFailBench** ([arXiv:2607.04686](https://arxiv.org/abs/2607.04686)) `[2026 preprint]` labels 1,000 tasks with a four-way taxonomy that maps almost exactly onto this section: **Tool-Skip** ("the model does not produce a valid executed tool call when one is needed"), Result-Ignore, Output-Fabrication, and **Unnecessary-Tool-Use**. Tool-Skip Rate is **11.80% for the best model (Grok-4.3) and 24.90% for the worst frontier model tested**, even where the aggregate Clean Tool-Use Rate looks healthy at 86.33%. The paper's framing is the useful part: "aggregate scores mask distinct failure patterns."

IFScale's omission bias (§4.2) is the same mode at scale: as constraint density rises, models "overwhelmingly err toward omission." AgentIF's ">30% incorrect condition checks" is the mode's proximate cause.

The tau-bench family measures the consequence for policy-following agents. **tau-bench** ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)): "even state-of-the-art function calling agents (like gpt-4o) succeed on <50% of the tasks, and are quite inconsistent (pass^8 <25% in retail). Our findings point to the need for methods that can improve the ability of agents to act consistently and follow rules reliably." **pass^8 under 25% is the number to hold onto**: a policy written in prose and satisfied once is not a policy satisfied reliably.

### 5.2 Over-firing - a gated stage runs when the gate is closed

Less discussed, equally measured. **KCIF** ([arXiv:2410.12972](https://arxiv.org/abs/2410.12972)) includes distractor instructions whose condition does not apply and finds "a 5-20% drop in small, medium, large, and frontier scale models" even where the instruction should have had no effect. Human annotators agreed on 93.33% of instances, so this is not ambiguity.

ToolFailBench's Unnecessary-Tool-Use Rate spans 0.00% (Qwen models) to 98.39% (Llama-3.1-8B) with "same-scale models differing by 89 percentage points on control accuracy" - over-firing is strongly model-family dependent, which matters for a pipeline that spawns different tiers per stage.

First-party corroboration and a named cause: Anthropic warns that current models "may now overtrigger" on aggressive language and names `"If in doubt, use [tool]"` as a cause; OpenAI names repetition as a cause - "Repeating instructions such as 'ask first,' 'do not mutate,' or 'wait for approval' can cause unnecessary approval requests for safe, expected actions."

### 5.3 Condition conflation - two independent conditions collapsed into one

This is the mode with the least direct benchmark, and the most indirect evidence.

ComplexBench measures it structurally: the drop from And (0.881) to Selection at depth >= 3 (0.694) to Selection-and-Chain at depth >= 3 (0.626) is what happens when conditions stop being independent and start nesting. The paper's own diagnosis of Selection difficulty is exactly conflation: "the main difficulty in Selection lies not only in choosing the correct branch but in executing it without interference from irrelevant branches."

Anthropic's authoring guidance treats the same risk as a naming problem: "Choose one term and use it throughout the Skill... Consistency helps Claude parse and follow instructions," with the bad example being a mix of "API endpoint", "URL", "API route", "path". Two dials named inconsistently across stages will be read as one.

The decision-theoretic version, from Anthropic: "If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better."

### 5.4 Precedence errors - a later rule silently overrides an earlier one

§4.6 supplies the numbers (IHEval's 21-65 point drops; 48% best open-source conflict resolution; the distance effect). The first-party guidance is unusually blunt for once: Anthropic says the outcome is "arbitrary"; GitHub says "Whenever possible, try to avoid providing conflicting sets of instructions"; OpenAI says state each instruction once and, where a genuine exception exists, **rewrite the rule to contain it** rather than adding an overriding rule elsewhere.

The one positional rule anyone states - GPT-4.1's later-in-prompt tendency - is contradicted by MOSAIC's per-family split and by IFScale's uniform primacy finding. There is no cross-model precedence mechanism a prose file can rely on.

### 5.5 Mitigations, with the numbers that support them

**What works (external checks):**

- **Deterministic pre-execution gates.** "Reason Less, Verify More" ([arXiv:2607.07405](https://arxiv.org/abs/2607.07405)) `[2026 preprint]` names the target failure precisely: agents "can violate the very policies they are deployed to enforce while appearing to complete the task successfully," producing "a silent wrong state" that "neither tools nor the agent's self-assessment reveal" - 78% of observed failures. The fix is "deterministic, read-only pre-execution gates that inspect the proposed call and current state before allowing a write," worth **+12.4 points on tau-bench airline (29.6% → 42.0%, P=0.0012)**, +19.2 points on tasks where gates activated, and +10.4 points even on a frontier model.
- **Tool-verified refinement, not self-critique.** Divide-Verify-Refine ([arXiv:2410.12207](https://arxiv.org/abs/2410.12207)) "doubles Llama3.1-8B's constraint adherence and triples Mistral-7B's performance," on the explicit premise that "LLMs cannot generate reliable feedback or detect errors."
- **State machines over prose control flow.** StateFlow ([arXiv:2403.11322](https://arxiv.org/abs/2403.11322)) separates "process grounding (via state and state transitions)" from "sub-task solving," beating ReAct by 13 points at 5x lower cost on InterCode SQL and 28 points at 3x lower cost on ALFWorld.
- **Trace verification of step order.** AgentLTL ([arXiv:2607.02599](https://arxiv.org/abs/2607.02599)) `[2026 preprint]` expresses "step ordering requirements, branching logic, iteration patterns" as temporal-logic rules over traces, with block-and-warn improving compliance in five of seven models.

**What works partially (structured self-emission):**

- **Checklists.** TICK/STICK ([arXiv:2410.03608](https://arxiv.org/abs/2410.03608)): decomposing an instruction into YES/NO questions raises judge-human agreement 46.4% → 52.2%, and self-refinement against the model's own checklist gives **+7.8 points absolute** on LiveBench reasoning. RLCF ([arXiv:2507.18624](https://arxiv.org/abs/2507.18624)) is "the only method to improve performance on every benchmark," including +4 points hard satisfaction on FollowBench.
- **Externalizing a running count.** Countdown prompting ([arXiv:2508.13805](https://arxiv.org/abs/2508.13805)): strict length compliance with GPT-4.1 goes "from below 30% under naive prompts to above 95%" - by converting an unverifiable constraint into a self-verifiable one.
- **Re-reading.** RE2 ([arXiv:2309.06275](https://arxiv.org/abs/2309.06275)) gains are real but modest (GSM8K davinci-003 19.48 → 24.79; ChatGPT +1.7-1.8).

**What does not work (self-report as evidence):**

- **Models Recall What They Violate** ([arXiv:2604.28031](https://arxiv.org/abs/2604.28031)) `[2026 single-author preprint]`: constraint recall is **97.3% across all models tested** while knows-but-violates rates span 8% to 99%. Reciting a rule does not predict obeying it. The same paper reports its LLM compliance judge had "near-perfect specificity (97%) but low sensitivity (15%)" - automated compliance checks massively under-count violations.
- **Specifying everything.** "Prompt underspecification" ([arXiv:2505.13360](https://arxiv.org/abs/2505.13360)): "simply specifying all requirements does not consistently help, as models have limited instruction-following ability and requirements can conflict."
- **Debiasing by instruction.** Option-order bias work ([arXiv:2309.03882](https://arxiv.org/abs/2309.03882)) found an explicit debiasing instruction made things marginally worse (RStd 5.5 → 6.1).

---

## Cross-cutting synthesis

| Question | What the evidence says | Confidence |
| --- | --- | --- |
| Are conditionals harder than flat rules? | Yes, 15-26 points of constraint satisfaction (AgentIF); Selection 0.765 vs And 0.881 (ComplexBench) | High - two independent benchmarks |
| What is the binding budget? | Number of conditionals, not lines. If-then guardrails approach zero pass rate by 10-20; real prompts average 5.1 (RealGuardrails) | High for the shape, single-source for the exact curve |
| Does nesting hurt more than breadth? | Yes. Independent dials (And 0.881) vs nested composition (Selection+Chain depth >= 3, 0.626) | High |
| Silent skip or over-firing - which dominates? | Both measured. Tool-Skip 11.8-24.9%; distractor conditions still cost 5-20 points | High |
| Can I rely on rule ordering? | No. "Arbitrary" (Anthropic); 48% best open-source conflict accuracy (IHEval); primacy vs recency flips by model family | High |
| Does restating a rule help? | Only as a short reminder, and only as insurance. Recall does not predict compliance (97.3% vs up to 99% violation) | Medium - key source is a 2026 preprint |
| Do checklists / forced emission help? | Yes, modestly (+4 to +8 points) and only when the emission is checkable | Medium-high |
| Do deterministic gates help? | Yes, most of any intervention measured (+12.4 points on tau-bench airline) | Medium - single 2026 preprint, but replicated across seeds within it |
| Table vs bullets vs prose? | No evidence either way for instruction files. Format spread is large (up to 76 points) but model-specific and non-transferable | Low - vendors decline to rule |
| Is length the problem? | Length is a proxy. Count dominates format and placement (Prompt Design at Scale); ISR ~0 above 6,000 words (AgentIF) | Medium-high |
| Where does everyone put the branch when they can? | In code, metadata, or a typed edge. Anthropic Agent Skills is the sole format with no such escape hatch | High |

**The one-sentence synthesis.** Prose conditionals are cheap up to roughly a handful and collapse somewhere between ten and twenty; the collapse is worse when conditions nest than when they sit side by side; both halves of a conditional fail measurably (evaluating the gate and honoring it); ordering carries no reliable precedence; and the only interventions with large effect sizes move the check outside the model that is being checked.

**Caveats on the evidence base.** Three of the sharpest results (deterministic pre-execution gates, trace verification, knows-but-violates) are 2026 preprints, two of them single-author; they are labeled where used and none of them carries a conclusion on its own. The RealGuardrails curve is one paper's figure, though its abstract, body text, and stated mechanism were all read off the PDF. Anthropic's own guidance is internally inconsistent on emphasis escalation (§1.1), and the vendors disagree outright on instruction placement (§1.4) - neither is settled, and this survey reports both sides rather than picking one. Finally, the conditional-instruction literature is thin on the specific question forge faces: nobody has published a study of conditional gating in an *orchestration doctrine file*, so §4 evidence transfers by analogy from constraint-following and system-prompt-robustness benchmarks, not by direct measurement.

---

## What forge could steal

1. **Budget conditionals, not lines.** The 76-line file is nowhere near Anthropic's 500-line cap, so length is not the risk. Count the live gates instead. Today's `SKILL.md` carries roughly nine (five detour flags, the trivial short path, three conditional lenses, plus DETOUR/KICKBACK returns). The spec's design adds a plan-depth lookup, a tests trigger, a challenge tier, four size/risk-keyed lens rules, the plan-floor coupling, the planner re-score, the escalation table, and the rewind exception - call it 12-15 live conditionals. RealGuardrails puts real-world prompts at 5.1 guardrails and shows collapse by 10-20. **Set an explicit gate budget and treat exceeding it as the trigger to split the file, exactly as three vendors independently prescribe.**

2. **Keep the dials separable, and say so in the file.** ComplexBench is the strongest empirical backing the spec's §2 already has: And (independent constraints) scores 0.881 where Selection-and-Chain at depth >= 3 scores 0.626. Two independent lookups plus one named coupling is measurably the right shape; a 9-cell case table is not. Write the two lookups as two small tables (OpenAI: "Use tables when the reader's job is to compare or choose among options") and the coupling as one sentence of prose.

3. **Fold the coupling into the rule, never state it as a later override.** The §2.3 plan floor is currently phrased as an exception to the size dial. OpenAI's own worked fix for exactly this shape is to rewrite the rule so the condition lives inside it, and Anthropic says a contradicted rule resolves arbitrarily. Write the plan rule once as its own complete statement - *plan depth is the deeper of the size lookup and the risk floor* - so the size table never has to be read against a paragraph that quietly amends it. Same treatment for §3.4: state the challenge-gating rule once, with the zero-adversary case inside it, rather than as an override of the implementer's KICKBACK behavior three sections later.

4. **Adopt one fixed conditional slot label and use it verbatim at every gated stage.** `**Apply if**:` appears five times identically in Anthropic's Opus 4.5 migration skill and is the most scannable convention in any published artifact. forge already has the leitwort discipline for this ("one concept, one name"); a gate marker is the same rule applied to structure. It also gives the doctrine-integrity self-audit a cheap canary: a gated stage missing its marker is mechanically detectable.

5. **Make RISK's path signals mechanical wherever the harness can compute them.** The RISK axis reads "primarily from PATH, CODEOWNERS-style" - which is glob-shaped, which is exactly what Cursor's `globs`, Copilot's `applyTo`, and CODEOWNERS all hoist out of prose. Anthropic's own `claude-api` skill resolves its skip condition with a `grep` and orders that grep before the expensive step; `pptx` gates its QA on `markitdown | grep`. forge's adapter already runs hooks; having it hand triage a computed sensitive-path hit list turns a judgment into a lookup on the axis where "default-to-deep" matters most.

6. **Give each gate a concrete bar, not an adjective.** Sonnet 5 "interprets prompts literally" and will apply a qualitative threshold conservatively; Anthropic's own test is "concrete enough to verify." `moderate` = "new logic in a bounded area" is the kind of phrase that reads differently at `mini` tier than at `ultra`. The spec's §4 dry-run table is the raw material: promote two or three of its rows into the file as worked examples of a band boundary, which Anthropic prefers over enumerated edge cases ("we do not recommend this").

7. **Force one structured emission of the resolved route, and make it checkable.** Triage already emits `SIZE`/`RISK`/`NEEDS-TESTS`. Extend that by one line: the orchestrator restates the resolved stage set once, before it spawns anything - the Anthropic checklist pattern, whose stated purpose is that "clear steps prevent Claude from skipping critical validation," and whose measured analogues (TICK/STICK +7.8, countdown prompting 30% → 95%) all work by making an unverifiable rule self-verifiable. **But do not treat the emission as evidence of compliance** - recall runs at 97.3% alongside violation rates up to 99%. Its value is that a later stage, a lens, or the adapter's stop-gate can compare the declared stage set against what actually ran.

8. **Point the rewind exception at a deterministic gate, not at a memory.** The §3.4 carve-out is the most fragile rule in the design: it fires on a conjunction (RISK re-scored to `critical` AND the challenge was gated `none`) and is bounded by a once-per-run guard - a state-carrying conditional evaluated late, which §5.4's distance finding says is the shape most likely to be missed entirely. The run dir is already the pipeline's state store. A one-line marker file written when the challenge runs (and read when the re-score lands) turns the conjunction into a file check, in the spirit of "Reason Less, Verify More"'s pre-execution gates (+12.4 points) and Microsoft's `WithDefault()` safety net.

9. **Phrase gates affirmatively and drop the emphasis reflex.** Google's "Instructions over Constraints" names the mechanism ("a list of constraints can clash with each other"); RealGuardrails measures the cost of a negated instruction at 25-41 points of compliance. And when a gate misfires, resist escalating to caps: Anthropic's current guidance is to dial aggressive language *back* because models now over-trigger, `skill-creator` calls ALL-CAPS "a yellow flag," and the shipped production skills contain zero such tokens. Anthropic's stated diagnosis for a rule that keeps getting ignored is file length, not weak wording.

10. **State the scope of every gate explicitly; it will not generalize.** "It does not silently generalize an instruction from one item to another." The planner re-score is authoritative for both axes, but the file must say so at each dependent stage (tests re-gate on the new SIZE; the review wave reads the final SIZE) rather than relying on "authoritative" carrying across four sections.

11. **Split before it hurts, one level deep - but split the file, not the turn.** All three vendors prescribe the same remedy at the same threshold. If the gate budget in steal #1 is exceeded, the routing table is the natural extract: `SKILL.md` stays the dispatcher and a sibling `ROUTING.md` holds the two dial tables plus the escalation table. Three constraints. References must stay one level deep from `SKILL.md`, since nested references get partially read via `head -100` and a gate condition in a twice-removed file may never be seen. The extracted file needs its own table of contents if it passes 100 lines. And the split must stay *spatial*: ComplexBench's Table 6 shows that decomposing a complex instruction into multi-round interaction made results **worse** (GPT-3.5-Turbo overall 0.682 → 0.652, worst on nested Selection at -0.067), and the CONCAT control in the multi-turn paper recovers 95.1% of performance precisely by collapsing turns back into one. Files the orchestrator reads up front are cheap; extra conversational rounds are not.

12. **Measure trigger-correctness separately from execution-correctness.** Anthropic states it directly: "Seeing a skill trigger tells you Claude found it, not that it did what you intended... measure two things separately." AgentIF's ">30% of errors are incorrect condition checks" is the same split with a number on it. The spec's §4 dry-run table currently checks the stage set that fires; add a column for whether the *bands* were read correctly, so a wrong route from a right band and a right route from a wrong band do not both read as one failure.

13. **Accept the ceiling, and let the adapter hold the floor.** Anthropic is unambiguous: instructions are advisory, hooks are deterministic, and "if the instruction is something that must run at a specific point... write it as a hook instead." Every framework in §3 says the same thing in its own vocabulary. forge's enforcement layer already exists; the question the doctrine edit should answer is which of the new gates (the ACCEPTANCE floor, the critical-risk HITL sign-off, the rewind trigger) are load-bearing enough to earn a deterministic backstop, and which are genuinely fine as prose.
