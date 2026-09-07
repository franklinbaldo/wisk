---
type: RunReading
id: run-readings/20260905-open-prs
run: runs/20260905-contract-guided-runtime
kind: open-prs
subject: Active implementation pull requests
reference: "wisk#33, okf-parser#248"
finding: "Wisk #33 exposed that okf-parser only exported observed types; upstream #248 now implements declared-but-unobserved contract export at the infrastructure layer."
---

# Open PRs reading

The active PR stack revealed a cross-repository contract-first requirement and moved the fix to the generic parser rather than duplicating it in Wisk.
