---
type: ConceptSpecification
concept_type: OutputPolicy
description: "Maps Wisk concept families to semantic output namespaces inside the repository knowledge tree."
---

# Concept: OutputPolicy

`OutputPolicy` keeps storage conventions explicit while preserving the three primary Wisk stages: `experiences/`, `wiki/`, and `skills/`.

## Required Frontmatter Fields

- `type`: `"OutputPolicy"`
- `id`: Stable identifier
- `title`: Human-readable name

## Route Fields

- `experience_path`
- `run_path`
- `handoff_path`
- `wiki_path`
- `skill_path`
- `proposal_path`
- `evaluation_path`
- `session_type_path`
- `run_spec_path`
- `context_policy_path`
- `access_policy_path`
- `output_policy_path`

Paths are relative to the knowledge bundle root. The default policy keeps all outputs beneath exactly three principal namespaces: `experiences`, `wiki`, and `skills`.
