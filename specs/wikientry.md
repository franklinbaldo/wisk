---
type: ConceptSpecification
concept_type: WikiEntry
description: "Persistent, distilled knowledge synthesized across repository-resident execution traces."
---

# Concept: WikiEntry

A `WikiEntry` represents consolidated, durable knowledge extracted from one or more Work `LoopRun` traces. Legacy `Experience` records may remain evidence during the 0.4 RC migration window. It answers: *what did repeated or contrasting executions teach us?*

## Required Frontmatter Fields

- `type`: Must be `"WikiEntry"`
- `id`: Unique identifier
- `title`: Concept or rule name
- `status`: Knowledge status (`"draft"`, `"active"`, `"deprecated"`)

## Optional Frontmatter Fields

- `tags`: List of topical tags
- `evidence`: Links to supporting Work `LoopRun` records; legacy `Experience` links remain readable during migration

## Content Structure

The body should describe:
1. **Summary**: concise distillation of the pattern or invariant;
2. **Context & Scope**: where and when it holds;
3. **Evidence & Lineage**: the Work traces (and migration-era Experience records, if any) that support it;
4. **Counterevidence**: important contradictions or scope limits when present.

Wiki synthesis should normally compare a corpus rather than turn one Work run's local observation into durable knowledge automatically.
