---
type: Experience
id: exp-2026-09-02-bootstrap-okf-boundary
title: Bootstrap decision separating wisk from okf-parser
timestamp: "2026-09-02T13:25:00-04:00"
status: success
context: "Initial bootstrap and repository architecture design for franklinbaldo/wisk"
---

# Bootstrap Experience: Decoupling Wisk from OKF Parser

## Context & Intent
In previous design discussions around OKF evolution, there was an initial exploration of placing agent-specific learning primitives (`WiskView`) directly inside `okf-parser`. This risked bloating a generic format parser with opinionated agent workflows.

## Action Taken
1. Created dedicated repository `franklinbaldo/wisk`.
2. Established strict architectural boundary: `okf-parser` handles pure format, graph, and relational infrastructure; `wisk` handles agent learning semantics (Experience → Wiki → Skill → Evaluation).
3. Configured OKF specs in `specs/` and knowledge layout in `knowledge/`.

## Findings
Decoupling maintains `okf-parser` as a lean, universal tool and frees `wisk` to evolve its domain semantics rapidly without upstream friction.

*Note: This is an authentic Phase 0 manual bootstrap experience.*
