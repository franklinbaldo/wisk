---
goal: "Reproduzir localmente a falha de test_execute_command_records_raw_fact_without_inventing_semantics e localizar onde exit_code deixa de ser int"
id: "run-goals/20260908t204958z-reproduzir-e-diagnosticar-a-fal/goal-diagnose-exit-code"
kind: "task-advance"
rationale: "O CI da arvore #70+#71 falha nesse teste com assert '0' == 0; e a unica falha atribuivel a #71."
run: "runs/20260908T204958Z-reproduzir-e-diagnosticar-a-falha-de-exit-code-n"
status: "achieved"
success_signal: "Um comando pytest local reproduz a falha e o trace registra a causa observada."
type: "RunGoal"
---

# RunGoal
