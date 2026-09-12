---
type: "RunObservation"
id: "run-observations/20260908t204958z-reproduzir-e-diagnosticar-a-fal/obs-envelope-no-stderr"
run: "runs/20260908T204958Z-reproduzir-e-diagnosticar-a-falha-de-exit-code-n"
kind: "friction"
summary: "wisk run escreve o stdout do subprocesso no stdout do proprio wisk e o envelope JSON no stderr. 'wisk run ... > out.json' captura a saida do comando, nao o envelope; um consumidor que faca json.loads no stdout quebra sempre que o comando imprime algo."
impact: "high"
observed_at: "2026-09-08T20:54:32.073546Z"
---

# RunObservation
