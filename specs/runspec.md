---
type: ConceptSpecification
concept_type: RunSpec
description: "Typed operational contract that defines how a class of agent runs should progress and what evidence makes them well formed."
---

# Concept: RunSpec

A `RunSpec` defines the operational protocol for a class of agent executions. A run is scaffolded from it before substantive work begins.

## Required Frontmatter Fields

- `type`: `"RunSpec"`
- `id`: Stable spec identifier
- `title`: Human-readable name
- `version`: Version of the operational contract
- `status`: `"active"`, `"experimental"`, or `"deprecated"`
- `required_reading_kinds`: Reading categories expected before the run can be considered informed
- `required_goal_kinds`: Goal categories the run must articulate
- `required_evidence_kinds`: Evidence categories expected for the run class
- `required_check_kinds`: Verification categories expected for the run class

## Optional Frontmatter Fields

- `skill`: Link to the `AgentSkill` this spec operationalizes
- `parent_spec`: Link to a more general `RunSpec`
- `allowed_result_states`: Domain-specific result states
- `completion_notes`: Additional semantic completion guidance

## Semantics

A `RunSpec` is not a prompt template. It is a typed contract whose unsatisfied requirements provide operational feedback during a live `LoopRun`.

`parent_spec` is operational inheritance. The four `required_*_kinds` lists are additive and de-duplicated in parent-to-child order, so a consumer can add one domain-specific reading, goal, evidence class, or check without copying the generic contract. Other child fields override inherited scalar or list values when supplied; omitted optional fields remain inherited. Cycles are invalid.

The runtime pins the complete effective RunSpec, not only the child document, into each new LoopRun. Historical runs therefore keep the exact inherited contract they started with even if either parent or child changes later.

Consumers should specialize only what is genuinely domain-specific. A local check such as a repository-specific proportionality review belongs in the consumer RunSpec; generic execution verification, Wiki grounding, and Skill lineage remain reusable upstream requirements.
