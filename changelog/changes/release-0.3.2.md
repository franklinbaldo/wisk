---
type: Changelog
version: 0.3.2
date: 2026-09-07
---

# Wisk 0.3.2

- Enforce the canonical Experience boundary: raw episodic observation stays separate from Wiki synthesis and Skill evolution.
- Ship a managed consumer-adoption AgentSkill that teaches correct Wisk specialization and links the Google Research WikiSkill paper as the architectural reference.
- Update the README to name and link the paper and teach project-local `uv` installation/execution instead of `uvx` for adopted consumers.
- Correct the dogfood bootstrap skill so it no longer creates a WikiEntry inside the same Experience run.
