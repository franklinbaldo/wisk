---
type: Changelog
version: 0.3.0
date: 2026-09-06
---

# Consumer golden path

- adds non-destructive `wisk init` for existing repositories;
- installs managed normative specs, canonical Experience/Wiki/Skill contracts, and a standard consumer profile;
- installs a managed `.wisk/.gitignore` so reproducible manifest/spec/system state does not pollute consumer diffs while local and learned state remains versionable;
- preserves versioned consumer/runtime knowledge (`local`, `experiences`, `wiki`, `skills`) when a fresh clone runs `init`;
- adds manifest-backed `wisk upgrade` with SHA-256 conflict detection and rollback-safe final writes;
- makes explicit `session start-next` fall back to on-demand Experience while preserving automatic `session next` semantics;
- autodiscovers `.wisk/knowledge` from the repository root in CLI commands;
- packages normative and canonical bootstrap assets in the wheel;
- makes scheduler selection prefer leaf SessionType specializations so consumer children replace managed defaults without priority tricks;
- makes `RunSpec.parent_spec` operational: required readings, goals, evidence, and checks append into the effective pinned contract;
- lets Handoffs targeting a parent SessionType activate compatible leaf specializations;
- documents the canonical cross-session Experience → Wiki → Skill evaluation lifecycle and consumer/core responsibility boundary.
