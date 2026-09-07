---
title: "RFC 0001 — Repository as Skill Runtime"
status: proposed
created: 2026-09-02
---

# RFC 0001 — Repository as Skill Runtime

## Summary

`wisk` turns a Git repository into a persistent environment in which agents can work, learn, negotiate changes, and progressively specialize their operating knowledge.

The central engineering thesis is:

> **The repository is the persistent container of the skill and of its evolution.**

A repository is not merely a place where a Wisk runtime stores files. It is the durable work environment agents already know how to operate through Git and repository hosting platforms: they inspect code and documents, create issues, implement changes, open pull requests, review, run CI, merge, revert, and leave an auditable history for the next agent.

`wisk` should make it easy to take an existing repository with a concrete objective, initialize the Wisk loop, point an agent at that repository, assign a role, and let the agent understand what to do next from the repository itself.

## Primary theoretical reference

This project is inspired by:

**Liyan Tang, Cyrus Rashtchian, Chun-Sung Ferng, Andrew Tomkins, Da-Cheng Juan, Tu Vu. _Wisk: Compiling Agent Experience into Persistent Knowledge for Skill Evolution_. 2026.**

Canonical preprint:

<https://arxiv.org/abs/2608.27454>

The paper introduces Wisk as a framework that separates:

1. raw agent execution experience;
2. accumulated persistent knowledge in a wiki;
3. executable skills;

and continuously consolidates experience into the wiki so later skill evolution can reuse prior learning.

The paper is the conceptual foundation for persistent knowledge accumulation and skill evolution.

This RFC adds an engineering interpretation that is specific to this project. Concepts such as **repository-as-skill-container**, GitHub issues as negotiated work, pull requests as concrete proposals, CI as part of evaluation, and predefined repository roles are project-level extensions. They must not be falsely attributed to the paper.

## Problem

Agents already operate repositories effectively when given Git/GitHub access. They can:

- inspect code and documentation;
- search history;
- create and triage issues;
- implement work on branches;
- open pull requests;
- review changes;
- run or inspect CI;
- merge safe changes;
- revert failed changes;
- leave durable artifacts for later sessions.

What remains difficult is configuring the **learning loop around that work**.

Without a persistent loop, a sequence of agent sessions often looks like:

```text
session A discovers a useful fact
  -> session ends
  -> fact is scattered in chat, logs, comments, or nowhere
  -> session B reconstructs context
  -> the same mistake may happen again
```

A repository may have excellent code and issue hygiene and still fail to accumulate reusable agent knowledge.

The hard problem is not giving an agent Git access. The hard problem is making the repository itself explain:

- what its objective is;
- what has already been learned;
- which operating procedures currently exist;
- what failed before;
- what work is pending;
- which role the current agent should perform;
- what evidence should be persisted;
- when knowledge should become a reusable skill;
- how a skill change should be evaluated;
- how failed skill evolution is rolled back without losing what was learned.

## Product thesis

`wisk` should make the following workflow easy:

```text
existing repository with a specific objective
  -> wisk init .
  -> repository gains persistent agent-learning structure
  -> agent receives Git/repository access
  -> agent is assigned a role
  -> agent reads repository state and relevant knowledge
  -> agent performs real work
  -> evidence and experience are persisted
  -> knowledge is consolidated
  -> issues/PRs evolve the repository and its skills
  -> evaluation decides acceptance or rollback
  -> next agent starts from a richer repository
```

The desired user experience is intentionally close to:

```bash
cd some-repository
wisk init .
```

After bootstrap, a user should be able to tell an agent something as small as:

> Work on this repository as an Explorer.

or:

> Work on this repository as a Reviewer.

The repository should contain enough machine-readable and human-readable state for the agent to know how that role behaves and what useful work is available.

## The repository is the skill container

For this project, a repository contains more than source code.

It is the durable environment of the skill:

```text
repository/
  objective and contracts
  source code / data / artifacts
  agent instructions
  OKF knowledge graph
  experiences
  persistent wiki knowledge
  executable agent skills
  skill proposals
  evaluations
  loop runs
  issues
  pull requests
  CI
  Git history
```

This does **not** mean every repository must use this exact physical layout. The semantic model matters more than the directory names.

The repository combines several useful persistence mechanisms:

### Git

Provides:

- versioning;
- history;
- diffs;
- authorship;
- branching;
- rollback;
- reproducibility.

### Issues

Represent negotiated or discoverable work:

- defects;
- opportunities;
- missing evidence;
- future improvements;
- architectural debt;
- proposed investigations.

Issues are not the knowledge base and must not replace the wiki.

### Pull requests

Represent concrete proposed changes to the repository:

- implementation changes;
- documentation changes;
- skill evolution;
- knowledge consolidation;
- evaluation artifacts.

A pull request is an auditable proposal, not necessarily a successful evolution.

### CI and checks

Provide deterministic evaluation surfaces for properties that can be automated:

- code correctness;
- formatting;
- schema validity;
- OKF conformance;
- graph invariants;
- regression fixtures;
- skill-evaluation checks when applicable.

CI is part of evaluation but is not equivalent to the full semantic `SkillEvaluation` concept.

## Wisk conceptual loop

The project adopts the core separation from the paper:

```text
raw execution experience
  -> persistent wiki knowledge
  -> executable skill
  -> evaluation
  -> accept or rollback
  -> next experience
```

A useful mental model is:

- **Experience** — what happened?
- **WikiEntry** — what did we learn?
- **AgentSkill** — how should we act?
- **SkillProposal** — how should that procedure change?
- **SkillEvaluation** — is the candidate actually better?
- **LoopRun** — what happened during this iteration?

These names are engineering concepts of this project unless explicitly present in the paper.

## Roles

Agents should not need to infer an unconstrained persona every time they enter a repository.

`wisk` should provide a small set of predefined roles that repositories may enable, specialize, or extend.

Initial role vocabulary:

### Explorer

Purpose: discover problems, opportunities, evidence gaps, and useful next work.

Typical actions:

- inspect repository state;
- inspect failures and recent experience;
- investigate unknowns;
- open or reclassify issues;
- record experience;
- avoid implementing large changes unless the role contract permits it.

### Implementer

Purpose: execute known work.

Typical actions:

- select actionable work;
- use applicable skills;
- implement changes;
- run validation;
- open/update pull requests;
- persist relevant execution experience.

### Reviewer / Evaluator

Purpose: determine whether proposed changes are correct and beneficial.

Typical actions:

- review pull requests;
- inspect evidence and prior knowledge;
- run or inspect tests and evaluations;
- identify regressions;
- recommend merge, revision, rejection, or rollback.

### Wiki Maintainer

Purpose: turn execution history into durable reusable knowledge.

Typical actions:

- consolidate experiences;
- identify repeated lessons;
- merge duplicate knowledge;
- preserve provenance;
- avoid prematurely turning every observation into policy.

### Skill Evolver

Purpose: evolve executable procedures from accumulated knowledge.

Typical actions:

- find knowledge not yet reflected in skills;
- propose skill creation or revision;
- link proposals to supporting knowledge;
- define evaluation requirements;
- avoid promoting isolated noise into global procedure.

### Curator / Planner

Purpose: inspect the state of the whole repository and improve the work system.

Typical actions:

- inspect issue/backlog health;
- identify stale or contradictory work;
- identify missing roles/skills;
- prioritize evidence collection;
- determine which role should operate next.

The role system should remain small and composable. Repositories may define domain-specific roles using the same underlying model.

## Role-driven entry

An agent entering a Wisk-enabled repository should be able to discover its working context from repository state rather than from a long external prompt.

Conceptually:

```text
agent receives repository access + role
  -> read repository objective
  -> read role contract
  -> retrieve relevant wiki knowledge
  -> retrieve applicable skills
  -> inspect issues / PRs / recent runs
  -> choose role-appropriate action
  -> execute
```

This is a core ergonomics target.

The external prompt should increasingly describe **intent and role**, while the repository carries the accumulated operational context.

## Bootstrap ergonomics

Configuring a Wisk loop manually is too expensive.

The CLI should aim toward:

```bash
wisk init .
```

`init` should inspect the existing repository and non-destructively establish the minimum runtime contract.

Depending on repository state and future `okf-parser` capabilities, initialization may create or configure:

- `AGENTS.md` integration;
- repository objective metadata;
- OKF knowledge bundle;
- specifications / declared schemas;
- role definitions;
- initial agent skills;
- `.okfignore`;
- CI validation hooks;
- Wisk configuration;
- instructions for agents entering via Git.

Initialization must not overwrite legitimate repository conventions without explicit intent.

A repository with existing agent instructions should be adapted, not replaced blindly.

## OKF as the structural substrate

Wisk is the semantic/runtime layer.

`okf-parser` is the structural knowledge layer.

The boundary is:

```text
OKF Markdown
  -> okf-parser
       -> concepts
       -> identity
       -> links
       -> validation
       -> Ibis relations
       -> typed relations
       -> NetworkX
       -> DuckDB
       -> schema export
  -> wisk
       -> roles
       -> experience semantics
       -> consolidation
       -> skill evolution
       -> evaluation
       -> rollback
       -> next-action ergonomics
```

`wisk` must aggressively reuse `okf-parser` rather than reimplement:

- frontmatter parsing;
- concept identity;
- link resolution;
- schema machinery;
- graph machinery;
- relational materialization;
- generic OKF validation.

If a missing capability is generic, improve `okf-parser` rather than hiding a parallel implementation inside Wisk.

Relevant parser integration issue:

- `franklinbaldo/okf-parser#214` — primitives for external Wisk runtimes over OKF.

## Repository state as a graph

The durable knowledge should be relational and traversable.

A typical lineage may be:

```text
LoopRun
  -> Experience
  -> WikiEntry
  -> SkillProposal
  -> AgentSkill
  -> SkillEvaluation
```

The exact graph may be richer, but relations should be explicit and auditable.

This allows agents to answer questions such as:

- why does this skill exist?
- which experiences support this knowledge?
- what changed after this failure?
- which proposal produced this skill version?
- which evaluation justified acceptance?
- what knowledge survived a rollback?
- what work is affected if this concept changes?

Prefer OKF links and parser-provided relations over duplicate ID registries.

## Asymmetric rollback

Skill state is reversible; accumulated knowledge is not casually erased.

If a skill evolution fails:

```text
candidate skill
  -> evaluation finds regression
  -> candidate rejected or rolled back
  -> evaluation remains
  -> experience remains
  -> wiki lesson remains
```

A failed proposal is itself useful experience.

The next proposal should be able to learn from that failure rather than rediscovering it.

## Dogfooding

`franklinbaldo/wisk` must be the first serious consumer of Wisk.

The project should use its own runtime as soon as each capability becomes usable.

Bootstrap may initially require manual OKF documents, but manual operation should be retired progressively:

```text
implement record-experience
  -> start using it for wisk development

implement consolidation
  -> start using it for wisk development

implement proposals/evaluation
  -> evolve wisk's own skills through them

implement MCP
  -> agents working on wisk prefer the MCP runtime
```

Dogfooding must represent real work, not synthetic demo entries.

## Issues and PRs are part of the work loop, not replacements for knowledge

A Wisk-enabled agent may autonomously:

- create issues;
- close obsolete issues;
- reclassify work;
- implement issues;
- create stacked PRs;
- review PRs;
- merge safe validated changes when repository policy permits;
- reject or close unrecoverable changes.

But durable lessons from that activity belong in the Wisk knowledge graph when they have future value.

Do not assume GitHub issue history alone is sufficient memory.

## Minimal target interaction

The long-term ergonomics target is approximately:

```bash
wisk init .
```

Then an agent receives:

```text
Repository: <git repository>
Role: Explorer
```

The agent should be able to determine from the repository:

- what the repository is trying to achieve;
- what the role permits and expects;
- what has already been learned;
- which work is available;
- which skills apply;
- which failures are known;
- which evidence is missing;
- what action would advance the repository.

The command given by the human should not have to reproduce the repository's accumulated memory every session.

## Non-goals

This RFC does not propose:

- replacing GitHub/Git with a custom task system;
- storing every conversation transcript forever;
- treating every execution observation as a skill;
- making Wisk equivalent to RAG;
- fine-tuning model weights;
- embedding Wisk taxonomy into `okf-parser` core;
- introducing a mandatory vector database;
- introducing a mandatory persistent SQL database;
- building an external orchestration service as the source of truth.

The repository remains the primary persistent coordination surface.

## Initial architecture

```text
Git repository
  |
  +-- repository objective / instructions
  |
  +-- GitHub/Git work surfaces
  |     +-- issues
  |     +-- branches
  |     +-- pull requests
  |     +-- CI
  |
  +-- OKF knowledge
  |     +-- experiences
  |     +-- wiki entries
  |     +-- agent skills
  |     +-- skill proposals
  |     +-- skill evaluations
  |     +-- loop runs
  |
  +-- wisk runtime
        +-- init
        +-- context
        +-- role selection/contract
        +-- experience recording
        +-- consolidation
        +-- skill evolution
        +-- evaluation
        +-- rollback
        +-- next-action assistance
        +-- CLI
        +-- MCP
```

## Implementation consequences

This RFC implies the following priorities.

### Priority 1 — bootstrap

Make a repository Wisk-aware quickly and non-destructively.

### Priority 2 — context

An entering agent must be able to reconstruct useful working context from repository state.

### Priority 3 — real experience persistence

The repo must start retaining useful execution experience early enough to dogfood itself.

### Priority 4 — roles

The runtime should make role-driven operation explicit and easy.

### Priority 5 — consolidation before skill mutation

Do not build a direct `trace -> rewrite skill` shortcut as the primary mechanism. Persistent knowledge is an intentional intermediate layer, following the core Wisk idea.

### Priority 6 — evaluation and asymmetric rollback

Skill evolution must be reviewable, testable, and reversible without erasing lessons.

### Priority 7 — MCP ergonomics

Modern agents should be able to enter and operate the repository through a small, discoverable MCP surface without knowing the internal directory topology.

## Success criterion

The project succeeds when this becomes normal:

1. choose a repository with a specific objective;
2. run `wisk init`;
3. give an agent repository access;
4. assign a role;
5. let the agent perform useful autonomous work;
6. observe that subsequent agents benefit from accumulated repository knowledge and improved procedures.

The strongest test is dogfooding:

> Does building and operating `wisk` make `wisk` progressively better at helping agents build and operate `wisk`?

If not, the runtime is not yet delivering the core product thesis.

## Open questions

1. What is the smallest useful set of built-in roles?
2. How should repositories specialize roles without copying large prompt templates?
3. What exact information should `wisk init` infer from an existing repository?
4. Which repository hosting concepts should remain adapters rather than core semantics?
5. How should Wisk select relevant context without prematurely requiring embeddings?
6. What should be the promotion threshold from WikiEntry to SkillProposal?
7. How should generic evaluation contracts coexist with domain-specific metrics?
8. Which additional generic primitives should move upstream into `okf-parser`?
9. How much of issue/PR lifecycle should Wisk expose directly versus leaving entirely to the agent's GitHub tooling?
10. How should repositories express permissions for roles so that autonomous work remains bounded and auditable?
