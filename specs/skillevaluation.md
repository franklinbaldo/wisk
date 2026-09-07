---
type: ConceptSpecification
concept_type: SkillEvaluation
description: "Optional explicit benchmark or decision record about a SkillProposal."
---

# Concept: SkillEvaluation

A `SkillEvaluation` is an optional explicit snapshot of comparative evidence or a decision record about a `SkillProposal`. It is useful when a consumer wants to materialize a benchmark, fixture-based comparison, regression review, or acceptance record as its own concept.

It is **not** a mandatory fourth phase of Wisk learning. The canonical learning roles are Experience → Wiki → Skill: Experience produces execution evidence, Wiki synthesizes and compares it, and a later Skill session decides the candidate's lifecycle.

## Required Frontmatter Fields

- `type`: Must be `"SkillEvaluation"`
- `id`: Evaluation identifier (e.g. `eval-2026-09-02-01`)
- `title`: Short evaluation title
- `proposal`: Link to `[SkillProposal](../proposals/...)`
- `decision`: Evaluation decision (`"accepted"`, `"rejected"`, `"inconclusive"`)
- `timestamp`: ISO-8601 timestamp

## Optional Frontmatter Fields

- `metrics`: Dictionary/mapping of scores or pass/fail counts
- `regressions`: Count or list of detected regressions

## Content Structure

When materialized, the body should present:
1. **Methodology**: Fixtures, historical scenarios, or tasks evaluated.
2. **Results & Regressions**: Comparison of baseline vs candidate performance.
3. **Conclusion & Decision**: The explicit benchmark/review conclusion.

A consumer may omit `SkillEvaluation` entirely when the relevant comparison is already captured in Experience lineage and WikiEntry synthesis.
