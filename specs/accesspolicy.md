---
type: ConceptSpecification
concept_type: AccessPolicy
description: "Declares repositories, paths, connectors, and tools a SessionType should or may be restricted to using."
---

# Concept: AccessPolicy

`AccessPolicy` is separate from context curation. It describes the desired access boundary and whether the host should treat it as advisory, scoped, or enforced.

## Required Frontmatter Fields

- `type`: `"AccessPolicy"`
- `id`: Stable identifier
- `title`: Human-readable name
- `mode`: `advisory`, `scoped`, or `enforced`

## Optional Frontmatter Fields

- `repositories`: Repository identifiers or URLs
- `paths`: Repository/workspace path scopes
- `connectors`: Connector/tool families relevant to the session
- `instructions`: Human-readable access guidance

Wisk always exposes the requested policy. Actual coercive enforcement is a capability of the host environment and must not be claimed when unavailable.
