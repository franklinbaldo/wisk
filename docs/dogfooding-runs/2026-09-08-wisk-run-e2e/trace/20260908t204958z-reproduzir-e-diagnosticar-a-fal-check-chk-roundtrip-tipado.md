---
type: "RunCheck"
id: "run-checks/20260908t204958z-reproduzir-e-diagnosticar-a-fal/chk-roundtrip-tipado"
run: "runs/20260908T204958Z-reproduzir-e-diagnosticar-a-falha-de-exit-code-n"
kind: "verification"
procedure: "grep exit_code/git_dirty_before nos arquivos RunExecution gravados e comparar com o envelope em memoria"
result: "Round-trip perde tipo: exit_code=1 vira '1', exit_code=0 desaparece do arquivo, git_dirty_before=false vira a string 'false' (truthy). Causa: _update_execution_next reescreve o arquivo a partir do frontmatter ja relido pelo loader OKF, que stringifica escalares e descarta falsy."
status: "fail"
evidence: "run-evidence/20260908t204958z-reproduzir-e-diagnosticar-a-fal/ev-execution-roundtrip"
goal: "run-goals/20260908t204958z-reproduzir-e-diagnosticar-a-fal/goal-diagnose-exit-code"
---

# RunCheck
