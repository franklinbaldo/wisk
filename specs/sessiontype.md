---
type: ConceptSpecification
concept_type: SessionType
description: "Defines the purpose and inherited operating contract for one class of Wisk session."
---

# Concept: SessionType

A `SessionType` describes what kind of execution session is being started. It selects a `RunSpec`, contributes prompt nudges, and composes context, access, output, and cadence policies without conflating those concerns.

## Required Frontmatter Fields

- `type`: `"SessionType"`
- `id`: Stable session type identifier
- `title`: Human-readable name
- `purpose`: Concise statement of what the session exists to accomplish
- `run_spec`: Link to the governing `RunSpec`

## Optional Frontmatter Fields

- `extends`: Parent `SessionType`; child configuration refines the parent
- `nudges`: Short instructions inherited and appended through the hierarchy
- `context_policy`: Link to a `ContextPolicy`
- `access_policy`: Link to an `AccessPolicy`
- `output_policy`: Link to an `OutputPolicy`
- `cadence_policy`: Link to a `CadencePolicy`

## Semantics

Inheritance is shallow by design. Scalar child fields override inherited values; `nudges` append in parent-to-child order. Policy links are ordinary inherited scalar configuration and remain independently inspectable. Cycles are invalid.

For scheduler selection, inheritance is also specialization: when a declared SessionType has one or more children, the scheduler considers the leaf specializations rather than making the parent compete with them. The parent remains available for explicit start by id. This lets a consumer extend a managed default SessionType with repository-specific RunSpecs, checks, or nudges without editing the managed parent and without relying on priority or lexical ordering to win selection.
