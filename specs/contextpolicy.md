---
type: ConceptSpecification
concept_type: ContextPolicy
description: "Declares what information is appropriate to surface to a SessionType and how strongly that curation is applied."
---

# Concept: ContextPolicy

`ContextPolicy` separates epistemic guidance from technical access control.

## Required Frontmatter Fields

- `type`: `"ContextPolicy"`
- `id`: Stable identifier
- `title`: Human-readable name
- `mode`: `advisory` or `curated`

## Optional Frontmatter Fields

- `include`: Context categories to surface by default
- `exclude`: Context categories that are off-limits or omitted from curated context
- `instructions`: Human-readable guidance shown to the agent

`advisory` explains the intended boundary without coercion. `curated` also filters the context returned by the Wisk runtime, while still not pretending to restrict external tools the host makes available.
