---
type: AccessPolicy
id: access-policies/development
title: Development repository access
mode: advisory
repositories:
  - franklinbaldo/wisk
paths: []
connectors:
  - github
instructions:
  - "Repository access is advisory by default; specialized SessionTypes may request narrower scopes."
  - "Do not claim host-level enforcement unless the execution environment actually provides it."
---

# Development access policy

Lightweight default access guidance for Wisk development.
