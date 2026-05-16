# Alp River

> *A river of agents, sized to the task.*

**Featured in:** [Alper Ortac's AI Stack](https://aistack.to/stacks/alper-ortac-unw0sl)

Multi-stage agent refinement for Claude Code, scaled by automatic complexity classification. Small changes pass quickly. Bigger ones add stages: clarification, planning, adversarial challenge, implementation, broad review, specialist review, self-heal.

The whole pipeline ships in one folder. Doctrine, 31 subagents, 8 slash commands, 8 quality hooks.

## Latest updates

- **0.2.1: a new reviewer asks whether each abstraction is earning its keep** - Architecture-reviewer flags shallow wrappers, single-call modules, premature seams, and leaky interfaces using the deletion test. Quality and structure get sharper: quality stays on tool / altitude / elegance, structure on size / nesting / layer crossings. Each finding now has one clear owner.
- **0.2.0: subagents pick up your project context, record novel findings, and draft ADRs** - Drop intent, stack, glossary, and ADRs into `docs/` and every agent that needs them reads them automatically. Reviewers and the implementer jot down terms and stack/intent drift they notice in passing - at the end of the pipeline you pick what to keep. `/alp-river:setup` writes the project docs interview-style; `/alp-river:adr` records a decision deliberately and rejects duplicates of active ADRs.
- **0.1.5: `/compact` doesn't reset you anymore** - After compacting, the rules and your in-progress work (intent, classification, plan) stick around. Was meant to work since 0.1.0 but quietly didn't. Pipeline numbering also stopped skipping mid-flow - the steps now read 0, 1, 2, 3, 4... in order.
- **0.1.4: clarification loops** - Intent and clarification keep asking until nothing new comes up, instead of stopping after one pass. Agents check the codebase and web first, so they only ask what those sources don't answer.
- **0.1.3: two-pass code review** - Correctness asks *does this work?* (bugs, type holes, dead code). Quality asks *is this the right way?* (hacky shortcuts when a clean path was right there, bloat, wrong tool). Splitting them stops one from softening the other.

Full history in [CHANGELOG.md](CHANGELOG.md).

## Install

In Claude Code:

```
/plugin marketplace add alp82/alp-river
/plugin install alp-river@alperortac
/reload-plugins
```

To pull updates later:
```
/plugin marketplace update alperortac
/reload-plugins
```

## How to use

Describe what you want. The classifier grades the task and the right specialists fire - doctrine is already loaded, nothing to enable.

Each stage is run by a dedicated agent: classifier judges scope, scanners pre-flight the area, clarifier surfaces ambiguity, planner designs the approach, challenger pokes holes, implementer builds, reviewers cross-check, fixer heals findings.

You stay in the loop at a few well-defined moments:

- **Intent confirmation** (always) - confirm or correct the one-sentence read; an interviewer digs deeper when your request has multiple readings, looping with you (cap 5 rounds) until intent settles and no new aspects emerge.
- **Clarifier questions** (M/L/XL when ambiguity remains) - the clarifier researches the codebase first, then asks only what's still open. It loops with you (cap 5 rounds) until clarity is reached, then the planner runs.
- **Plan selection** (XL) - pick one of the proposed approaches.

Everything else runs to completion. Reviewer findings feed the fixer automatically.

Override the grade with natural language: *treat this as L*, *skip clarify*, *go straight to plan*.

## How the river flows

A complexity classifier reads each task and grades it **S**, **M**, **L**, or **XL**. The grade decides which stages run.

A SessionStart hook reads `AGENTS.md` and injects it into every Claude session as foundational context. Doctrine is always loaded, no per-file imports, no skill matching. After `/compact`, it fires again to restore doctrine plus the canonical workflow state (intent, classification, approved plan).

In every diagram below, **dotted edges are conditional** (a gate fires the agent only when its trigger matches).

## S - small

Main agent implements directly. Quality hooks fire on edits.

```mermaid
flowchart TB
    intent --> classify[complexity-classifier]
    classify --> impl[main agent implements]
    impl --> hooks[quality hooks]
```

## M - medium

Pre-flight scans run in parallel. Implementation, then broad review fan-out, then conditional specialists, then self-heal.

```mermaid
flowchart TB
    intent -.-> intv[interviewer]
    intent --> classify[complexity-classifier]
    intv --> classify
    classify --> reuse[reuse-scanner] & health[health-checker] & proto[prototype-identifier] & rsrch[researcher]
    proto -.-> ptype[prototyper]
    reuse & health & proto & rsrch --> impl[main agent implements]
    ptype -.-> impl
    impl --> bp
    subgraph bp[broad pass]
        direction LR
        test[test-verifier]
        correct[correctness-reviewer]
        qual[quality-reviewer]
        accept[acceptance-reviewer]
    end
    bp -.-> sp
    subgraph sp[specialists - gated]
        direction LR
        sr[structure-reviewer]
        ar[architecture-reviewer]
        cr[consistency-reviewer]
        rr[reuse-reviewer]
        sec[security-reviewer]
        perf[performance-reviewer]
        a11y[accessibility-reviewer]
        dc[design-consistency-reviewer]
        ux[ux-reviewer]
    end
    bp --> heal[fixer]
    sp --> heal
    heal --> cap[capture-agent]
```

## L - large

Adds clarification, planning, and adversarial challenge. Implementer subagent takes the build. Plan-adherence-reviewer joins the broad pass.

```mermaid
flowchart TB
    intent -.-> intv[interviewer]
    intent --> classify[complexity-classifier]
    intv --> classify
    classify --> reuse[reuse-scanner] & health[health-checker] & proto[prototype-identifier] & rsrch[researcher]
    proto -.-> ptype[prototyper]
    reuse & health & proto & rsrch --> clari[requirements-clarifier]
    ptype -.-> clari
    clari --> plan[planner]
    plan --> chal[plan-challenger]
    chal --> impl[implementer]
    impl --> bp
    subgraph bp[broad pass]
        direction LR
        test[test-verifier]
        correct[correctness-reviewer]
        qual[quality-reviewer]
        accept[acceptance-reviewer]
        adher[plan-adherence-reviewer]
    end
    bp -.-> sp
    subgraph sp[specialists - gated]
        direction LR
        sr[structure-reviewer]
        ar[architecture-reviewer]
        cr[consistency-reviewer]
        rr[reuse-reviewer]
        sec[security-reviewer]
        perf[performance-reviewer]
        a11y[accessibility-reviewer]
        dc[design-consistency-reviewer]
        ux[ux-reviewer]
    end
    bp --> heal[fixer]
    sp --> heal
    heal --> cap[capture-agent]
```

## XL - extra large

Planner presents 2-3 approaches. Challenger reviews each. User picks. Visual verifier joins the specialist pass for UI changes.

```mermaid
flowchart TB
    intent -.-> intv[interviewer]
    intent --> classify[complexity-classifier]
    intv --> classify
    classify --> reuse[reuse-scanner] & health[health-checker] & proto[prototype-identifier] & rsrch[researcher]
    proto -.-> ptype[prototyper]
    reuse & health & proto & rsrch --> clari[requirements-clarifier]
    ptype -.-> clari
    clari --> plan["planner: 2-3 approaches"]
    plan --> chal["plan-challenger reviews each"]
    chal --> pick[user picks approach]
    pick --> impl[implementer]
    impl --> bp
    subgraph bp[broad pass]
        direction LR
        test[test-verifier]
        correct[correctness-reviewer]
        qual[quality-reviewer]
        accept[acceptance-reviewer]
        adher[plan-adherence-reviewer]
    end
    bp -.-> sp
    subgraph sp[specialists - gated]
        direction LR
        sr[structure-reviewer]
        ar[architecture-reviewer]
        cr[consistency-reviewer]
        rr[reuse-reviewer]
        sec[security-reviewer]
        perf[performance-reviewer]
        a11y[accessibility-reviewer]
        dc[design-consistency-reviewer]
        ux[ux-reviewer]
        visual[visual-verifier]
    end
    bp --> heal[fixer]
    sp --> heal
    heal --> cap[capture-agent]
```

## Agents

31 subagents organized by phase of work. Italic = conditional / gated. Tier shows the model that runs by default.

### Understand (Steps 0-1)

| Agent | Tier | Role |
|-------|------|------|
| *interviewer* | opus | Level 2 intent - probes scope, users, success criteria when the request has multiple readings or the Level 1 answer shifts scope. |
| complexity-classifier | opus | Grades each task S / M / L / XL and gates which downstream stages run. |

### Prepare (Steps 2-3)

| Agent | Tier | Role |
|-------|------|------|
| reuse-scanner | sonnet | Finds reusable code and quick-win refactors before implementation. |
| health-checker | haiku | Scores code-health of the touched area, surfaces cleanup targets. |
| prototype-identifier | haiku | Flags external APIs / SDK novelty that need a tracer bullet. |
| researcher | haiku | Pulls library / framework / domain knowledge from the web. |
| *prototyper* | sonnet | Builds tracer-bullet prototypes in `.prototypes/` when prototype-identifier flags external surface. |
| requirements-clarifier | opus | Surfaces ambiguity, edge cases, and proposed acceptance criteria as a numbered question list before the planner runs. |

### Design (Steps 4-5)

| Agent | Tier | Role |
|-------|------|------|
| planner | opus | Designs the implementation blueprint. On XL, presents 2-3 approaches with a recommendation. |
| plan-challenger | opus | Adversarial review - pokes holes, names failure modes, proposes simpler alternatives. |

### Build (Step 6)

| Agent | Tier | Role |
|-------|------|------|
| implementer | opus | Executes the approved plan on L/XL. Can kick back to planner via tiered escalation. |

### Verify (Steps 7-9)

**Broad pass** - runs in parallel on every M/L/XL.

| Agent | Tier | Role |
|-------|------|------|
| test-verifier | sonnet | Runs the project's test suite, fails fast. |
| correctness-reviewer | sonnet (M) / opus (L/XL) | Bugs, type holes, dead code, project convention adherence. |
| quality-reviewer | opus | Engineering judgment - hacky shortcuts, bloat, wrong tool for the job, unelegant solutions. Reads imports and deps first. |
| acceptance-reviewer | opus | Verifies every requirement and acceptance criterion maps to actual code; flags scope drift. |
| *plan-adherence-reviewer* | sonnet | L/XL only. Checks the implementer followed the plan's file list, signatures, and ordering. |

**Specialist pass** - fires only when its trigger matches: a broad-pass finding in its domain, or touched files inside its scope.

| Agent | Tier | Trigger |
|-------|------|---------|
| structure-reviewer | sonnet | Broad pass flagged structure / boundaries; or files / functions over size thresholds. |
| architecture-reviewer | opus | Touched files introduce new exports / wrappers / seams; or broad pass flagged shallow abstraction. Uses depth + the deletion test. |
| consistency-reviewer | sonnet | Touched files affect naming / error handling / return-shape patterns. |
| reuse-reviewer | sonnet | Broad pass flagged duplication; or new code resembles existing utilities. |
| security-reviewer | opus | Touched files include auth / permissions / session / input handling. |
| performance-reviewer | sonnet | Touched files include database / query / hot-path code. |
| accessibility-reviewer | sonnet | Touched files include UI components. |
| design-consistency-reviewer | sonnet | Touched files include UI components. |
| ux-reviewer | sonnet | Touched files include UI components. |
| visual-verifier | sonnet | XL + UI; uses playwright-cli to screenshot and verify. |

**Self-heal** - applies fixes once the broad and specialist passes have produced findings.

| Agent | Tier | Role |
|-------|------|------|
| fixer | sonnet (M) / opus (L/XL) | Applies targeted fixes for aggregated findings. Emits a re-run set. |

### Capture (Steps 10-11)

| Agent | Tier | Role |
|-------|------|------|
| capture-agent | opus | Collects novel project-context items (glossary terms, stack/intent drift) surfaced incidentally by upstream agents. Two phases - proposes, then writes after user approval. Never creates `docs/`. |

### Separate flows

Each is triggered by its own command and runs outside the main pipeline.

| Agent | Tier | Role |
|-------|------|------|
| investigator | opus | Root-cause debugging - forms hypotheses, attempts minimal repro, traces to the actual cause. Stops at diagnosis; outputs complexity + severity for routing to `/fix` or `/feature`. Used by `/investigate`. |
| setup-agent | opus | Interactive bootstrap of docs/INTENT.md, docs/STACK.md, docs/GLOSSARY.md via 5-invocation guided interview. Used by `/alp-river:setup`. |
| adr-drafter | opus | Drafts a single ADR from a decision summary, mirroring the canonical template. Read-only - emits a draft or hard-rejects on duplicates of active ADRs. Used by `/alp-river:adr`. |

## Slash commands

```
/alp-river:setup        Interactive bootstrap of docs/INTENT.md, docs/STACK.md, docs/GLOSSARY.md
/alp-river:adr          Draft and write a single architectural decision record
/alp-river:feature      Full pipeline (L/XL - clarify, plan, challenge, build, review)
/alp-river:fix          Lighter pipeline for fixes and small changes (S/M)
/alp-river:plan         Design-only - each stage driven by a specialist agent
/alp-river:investigate  Root-cause debugging - stops at diagnosis, no patch
/alp-river:review       Review current changes for correctness + engineering quality
/alp-river:verify       Visual verification of UI changes via playwright-cli
```

## Structure

```
alp-river/
├── .claude-plugin/plugin.json
├── AGENTS.md              <- doctrine + reviewer contract
├── hooks/
│   ├── hooks.json         <- 7 events: SessionStart, PreToolUse, PostToolUse, ...
│   └── *.sh               <- inject-doctrine, auto-format, block-git-writes, ...
├── agents/                <- 30 subagent definitions
├── commands/              <- 8 slash commands
└── templates/             <- copy into your project's docs/ for project-context injection
```

## Local development

Clone the repo and pass `--plugin-dir`:

```bash
git clone https://github.com/alp82/alp-river.git
claude --plugin-dir ./alp-river
```

## Author

Alper Ortac &middot; [x.com/alperortac](https://x.com/alperortac)
