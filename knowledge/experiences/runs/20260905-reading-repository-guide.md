---
type: RunReading
id: run-readings/20260905-repository-guide
run: runs/20260905-contract-guided-runtime
kind: repository-guide
subject: Wisk architecture and runtime
reference: docs/architecture.md
finding: "Wisk now treats contract-guided live execution as a primary responsibility while persistent learning remains the downstream lifecycle."
---

# Repository guide reading

The architecture establishes `RunSpec -> LoopRun -> typed run components -> learning` as the runtime boundary.
