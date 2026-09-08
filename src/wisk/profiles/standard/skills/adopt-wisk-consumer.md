---
type: AgentSkill
id: skill-adopt-wisk-consumer
title: Adopt Wisk in a consumer repository
version: "1.1.0"
status: active
tags: [wisk, consumer, adoption, bootstrap, specialization]
derived_from:
  - rfc-0007-work-traces-learning-pivot
---

# Skill: Adopt Wisk in a Consumer Repository

## Purpose

Apply Wisk without recreating its persistent-learning architecture locally or mixing the canonical Work, Wiki, and Skill responsibilities.

Wisk is inspired by the Google Research paper **“WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution”** (Tang et al., 2026): https://arxiv.org/abs/2608.27454. RFC 0007 translates the paper's Raw / Wiki / Skills separation into Wisk's Work trace model.

## Procedure

1. Install Wisk as a normal project dependency from PyPI and run it through the project's own environment. With `uv`, prefer `uv add wisk`, `uv sync`, `uv run wisk init`, and ordinary execution with `uv run wisk start`; do not introduce a second `uvx` runtime path for an adopted project.
2. Run `wisk init` idempotently. Treat Wisk-managed files as product-owned and keep consumer specialization under `.wisk/knowledge/local/`. The repository-resident learning state is the durable substrate; provider-local chat history is not.
3. Before writing a local SessionType or RunSpec, classify its cognitive responsibility:
   - **Work / Worker** performs useful external work. A closed Work `LoopRun` plus its typed `Run*` children is the Raw Layer. Record goals, evidence, checks, relevant `RunObservation`s and the exact `RunSkillUse` provenance while context is hot. Do not synthesize Wiki or globally judge skills from one run.
   - **Wiki / Wiki Maintainer** studies a corpus of closed Work traces and existing Wiki knowledge. It consolidates recurrence, contrast, root causes, counterevidence, scope and failure modes into `WikiEntry`. It does not perform pending operational handoff work and does not change executable skills.
   - **Skill / Skill Evolver** uses Wiki knowledge, selected supporting Work traces, current skills and prior `SkillProposal` outcomes to make one atomic procedural intervention. Candidate creation is not promotion; validation/gating remains explicit.
4. Extend `session-types/work`, `session-types/wiki`, or `session-types/skill` (normally through the matching standard specialization) instead of recreating the role. `session-types/experience` is only a 0.4 RC compatibility bridge.
5. Never put instructions such as “when reusable knowledge is discovered, write WikiEntry or AgentSkill” into a Work specialization. The Worker records the local observation; a later independent Wiki session decides whether it generalizes.
6. Keep the Worker context intentionally asymmetric: applicable skills and handoff continuation may be present, but accumulated Wiki is excluded by default. Wiki and Skill roles receive the synthesis/history surfaces they need.
7. Record `RunSkillUse` only for procedure that actually guided the run, with the exact version and active/experimental state. Use `RunObservation(kind: skill_feedback)` for local helpful/harmful evidence; do not infer global promotion from it.
8. Treat handoffs as operational responsibility. Resolving CI, modifying a branch, merging a PR, or finishing prior work is Work. An active handoff must not make a Wiki session eligible merely because synthesis may later be useful.
9. Use `wisk migrate` before upgrading a 0.3.x knowledge bundle. The RC preserves old `Experience` documents as readable historical provenance while new standard Work runs stop producing a redundant Experience summary.
10. Verify the adoption with `wisk start`, `wisk check`, and role-specific `wisk context`. A fresh standard consumer should select Work; Worker context should not contain Wiki; later Wiki context should be able to see closed Work traces.
11. When accumulated Wiki knowledge justifies a skill candidate, preserve the full lineage: motivating WikiEntry → SkillProposal/gating → experimental AgentSkill → RunSkillUse in later Work → subsequent Wiki synthesis.
12. If a recurring adoption mistake requires repeated local workaround instructions, improve Wisk's managed profile, this adoption skill, or its tests rather than teaching every consumer independently.

## Invariant

A consumer adoption is structurally sound when ordinary useful work leaves a queryable raw Work trace without simultaneously performing Wiki synthesis or Skill evolution, and later independent Wiki/Skill sessions can reconstruct why procedure changed and what happened when the changed procedure was exercised.
