---
type: SessionType
id: session-types/experience
title: Experience (deprecated compatibility alias)
purpose: "Compatibility bridge for pre-0.4 consumers; ordinary execution is now the canonical Work role."
run_spec: run-specs/experience
extends: session-types/work
nudges:
  - "Deprecated in 0.4: prefer session-types/work for new execution sessions."
---

# Experience compatibility alias

`session-types/experience` remains readable during the 0.4 RC migration window so existing consumer SessionTypes can resolve. Its semantics are inherited from `session-types/work`.

New bundles and documentation should use Work. A run is the raw execution trace; Wisk no longer requires a separate canonical Experience artifact to restate what happened.
