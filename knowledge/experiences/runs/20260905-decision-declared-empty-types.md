---
type: RunDecision
id: run-decisions/20260905-declared-empty-types
run: runs/20260905-contract-guided-runtime
question: "Where should support for schema export before the first type instance live?"
decision: "Implement declared-but-unobserved type discovery in okf-parser and keep Wisk limited to execution semantics."
rationale: "Contract-first schema export is generic OKF infrastructure used by JSON Schema, Zod and Pydantic, so placing it in Wisk would duplicate parser responsibilities."
goal: run-goals/20260905-contract-runtime
alternatives:
  - "Create placeholder Run* documents only to make export discover the types"
  - "Reimplement spec/schema discovery inside Wisk"
evidence:
  - run-evidence/20260905-start-check-runtime
---

# Contract ownership decision

The failing Wisk lower-bounds test exposed an infrastructure gap rather than a domain-specific runtime gap.
