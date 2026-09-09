---
type: ConceptSpecification
concept_type: RunCheck
description: "A verification performed during a live run, including procedure, result, and supporting evidence."
---

# Concept: RunCheck

A `RunCheck` records an explicit verification of the current run state.

## Required Frontmatter Fields

- `type`: `"RunCheck"`
- `id`: Check identifier
- `run`: Link to the `LoopRun`
- `kind`: Check category defined by the applicable `RunSpec`
- `procedure`: Command, query, review procedure, or other verification method
- `result`: Concise observed result
- `status`: `"pass"`, `"fail"`, or `"inconclusive"`

## Optional Frontmatter Fields

- `evidence`: Link to supporting `RunEvidence`
- `goal`: Link to the `RunGoal` being verified
- `observed_at`: ISO-8601 timestamp of the verification

## Semantics

Checks turn evidence into explicit verification. The generic type is domain-neutral; RunSpecs define which checks matter for a particular class of work.

## Standing check per kind

A `required_check_kind` is satisfied only when the run's **standing** check of that
kind has `status: pass`. The standing check is the latest one recorded for the kind,
ordered by `observed_at` and falling back to record order when timestamps are absent.

Checks are append-only, so a kind that failed is not corrected by editing the failed
record: record a new check of the same kind, and the later one stands. `fail` and
`inconclusive` keep the run open, which is why the RunOutcome carries no list of the
checks that sustain it — presence of a check never counted as verification, and now
neither does the runtime treat it that way.
