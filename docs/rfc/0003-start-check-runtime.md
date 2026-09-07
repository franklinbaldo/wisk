---
type: ConceptSpecification
concept_type: RuntimeRFC
description: "Start/check semantics for contract-guided Wisk runs."
---

# RFC 0003 — Start/check runtime

Wisk should expose a minimal runtime protocol for contract-guided execution:

```text
start(task, run_spec?) -> LoopRun scaffold
check(run) -> structural diagnostics + unsatisfied RunSpec requirements
```

`start` creates the live `LoopRun` before substantive work begins. It records the task and governing `RunSpec`, but leaves progressive state empty on purpose.

`check` has two layers:

1. delegate structural OKF validation to `okf-parser`;
2. evaluate Wisk-specific completion semantics from the governing `RunSpec` against typed run components already present in the bundle.

Wisk does not duplicate Markdown parsing, frontmatter validation, link resolution or schema validation. Those remain `okf-parser` responsibilities.

The semantic layer reports missing reading kinds, goal kinds, evidence kinds, check kinds and outcome state. Those unsatisfied requirements are intended to guide the agent's next action.

CLI and FastMCP should expose the same protocol.
