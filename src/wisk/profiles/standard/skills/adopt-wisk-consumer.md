---
type: AgentSkill
id: skill-adopt-wisk-consumer
title: Adopt Wisk in a consumer repository
version: "1.0.0"
status: active
tags: [wisk, consumer, adoption, bootstrap, specialization]
---

# Skill: Adopt Wisk in a Consumer Repository

## Purpose

Apply Wisk to an existing repository without recreating its learning architecture locally or mixing the canonical Experience, Wiki, and Skill responsibilities.

Wisk is inspired by the Google Research paper **“WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution”** (Tang et al., 2026): https://arxiv.org/abs/2608.27454. When the intended semantics of raw experience, wiki synthesis, or skill evolution are unclear, consult that paper and Wisk's current RFCs before inventing a local interpretation.

## Procedure

1. Install Wisk as a normal project dependency from PyPI and run it through the project's own environment. With `uv`, prefer `uv add wisk`, `uv sync`, `uv run wisk init`, and ordinary execution with `uv run wisk start`; do not introduce a separate `uvx` runtime path for a project that has adopted Wisk as a dependency.
2. Run `wisk init` idempotently and treat Wisk-managed files as product-owned. Keep consumer-owned specialization under `.wisk/knowledge/local/` and learned runtime state in its designated Experience, Wiki, and Skill namespaces.
3. Before writing a local SessionType or RunSpec, classify its responsibility:
   - **Experience** executes real work and records truthful raw episodic evidence about what happened. It may preserve continuation state such as a Handoff, but it does not decide what becomes durable knowledge or modify reusable procedure merely because a lesson appears useful.
   - **Wiki** reads multiple Experiences and synthesizes durable knowledge, patterns, comparisons, counterevidence, and failure modes into WikiEntry state.
   - **Skill** uses durable knowledge and supporting evidence to create, refine, promote, reject, deprecate, or replace AgentSkill procedure.
4. Extend the canonical or standard parent matching that responsibility instead of recreating the role. Add only domain-specific purpose, readings, evidence, checks, cadence, context, or operational constraints that carry consumer meaning.
5. Never put instructions such as “when reusable knowledge is discovered, persist WikiEntry or AgentSkill” into an Experience specialization. That collapses raw observation, synthesis, and intervention into one session and defeats the separation that gives WikiSkill/Wisk its learning semantics.
6. Keep domain authority in the consumer repository. Local Wisk specialization should point to living domain contracts rather than copy them into a second orchestration layer.
7. After specialization, verify `wisk start` selects/resumes the intended leaf SessionType and effective RunSpec, and inspect the effective context so Experience is not accidentally receiving synthesis-only state.
8. If a recurring adoption mistake cannot be prevented by a small local specialization, improve Wisk's managed profile, this adoption skill, or its tests rather than teaching every consumer the workaround independently.

## Invariant

A consumer adoption is structurally sound when ordinary domain work can produce raw Experience evidence without performing Wiki synthesis or Skill evolution in the same role, while later Wiki and Skill sessions can consume that evidence through the canonical lineage.
