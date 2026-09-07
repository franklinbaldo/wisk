---
type: Experience
id: experiences/20260905-contract-first-types
title: Contract-first types must exist before their first instance
timestamp: "2026-09-05T18:02:00Z"
status: confirmed
skill_used: ""
skill_version: ""
task: "Implement and dogfood contract-guided Wisk runs"
error_code: ""
context: "While making RunReading, RunGoal, RunDecision, RunEvidence, RunCheck and RunOutcome exportable before a live run produced them, Wisk exposed that okf-parser only exported observed types. The correct fix was upstream: ConceptSpecification plus sibling .schema.sql must define an exportable type even with zero instances. okf-parser PR #248 implemented and verified this behavior."
---

# Contract-first types must exist before their first instance

A runtime that scaffolds future execution state needs its contracts before the first state record exists. Declared type identity therefore belongs to the specification/schema layer, while observed documents provide instances rather than permission for the type to exist.
