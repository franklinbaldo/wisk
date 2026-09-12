---
type: "RunObservation"
id: "run-observations/20260908t204958z-reproduzir-e-diagnosticar-a-fal/obs-run-honesto-nao-fecha"
run: "runs/20260908T204958Z-reproduzir-e-diagnosticar-a-falha-de-exit-code-n"
kind: "friction"
summary: "Um RunCheck kind 'verification' com status fail NAO satisfaz o requisito check:verification (runtime.py:79 exige status pass). Uma sessao de diagnostico cujo resultado verdadeiro e 'esta quebrado' nao consegue fechar nem como partial+handoff: o mesmo gate bloqueia o RunOutcome. O unico caminho para fechar e registrar um check verde sobre outra proposicao, ou seja, o contrato pressiona o agente a mentir."
impact: "high"
observed_at: "2026-09-08T20:58:17.490777Z"
---

# RunObservation
