---
type: RunCheck
id: run-checks/20260905-tests
run: runs/20260905-contract-guided-runtime
kind: tests
procedure: "Run the Wisk CI test suite and lower-bound test suite against the live run state."
result: "Both the main test job and test-lower-bounds job passed on PR #34 CI run #48."
status: passed
evidence: run-evidence/20260905-contract-verification
goal: run-goals/20260905-contract-runtime
---

# Tests check

The first persisted live run passed the repository's normal and lower-bound test suites.
