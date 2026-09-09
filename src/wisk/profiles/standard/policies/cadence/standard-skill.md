---
type: CadencePolicy
id: cadence-policies/standard-skill
title: Standard Skill cadence
on_demand: false
threshold_metric: work-runs-since-last-run
threshold_gte: 6
priority: 150
handoff_compatible: false
---

# Standard Skill cadence

Six newly closed Work traces since the previous Skill run make procedural evolution eligible. When Wiki is also due, its higher priority causes fresh synthesis to run first. Operational handoffs remain Work responsibility.
