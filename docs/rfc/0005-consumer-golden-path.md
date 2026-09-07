---
title: "RFC 0005 — Consumer golden path"
status: proposed
created: 2026-09-06
---

# RFC 0005 — Consumer golden path

## Summary

Wisk should be opinionated about how a repository adopts the learning runtime while remaining neutral about the repository's domain.

A consumer should not have to reproduce Wisk's internal directory layout, copy normative specs by hand, pin private implementation details, or rediscover the canonical Experience → Wiki → Skill cycle. The normal path should be:

```bash
wisk init .
wisk session start-next "Faça o melhor avanço possível neste repositório"
```

The consumer owns domain specialization. Wisk owns the learning architecture, compatible contracts, bootstrap, upgrade mechanics, and a useful default scheduling profile.

## Product boundary

### Wisk owns

- the canonical Experience, Wiki, and Skill roles;
- their canonical RunSpecs;
- normative specs compatible with the installed runtime;
- a recommended standard profile that schedules the three roles coherently;
- bootstrap and upgrade of Wisk-managed files;
- the manifest that identifies managed state;
- safe conflict detection before managed files are replaced;
- CLI ergonomics that let an explicit `session start-next` fall back to ordinary Experience work when no higher-value maintenance session is due.

### The consumer owns

- repository objectives and domain meaning;
- domain-specific readings, checks, tools, and evidence;
- access/institutional policy;
- merge, publication, deployment, or approval rules;
- local SessionType and RunSpec specializations;
- local cadence changes when the standard profile is not appropriate.

## Managed and local state

Bootstrap creates `.wisk/` with two conceptual surfaces:

```text
.wisk/
  manifest.json
  specs/                  # managed normative contracts
  knowledge/
    system/               # managed Wisk roles/profile
    local/                # consumer-owned specializations
    experiences/          # runtime-produced state
    wiki/                 # runtime-produced durable knowledge
    skills/               # runtime-produced/local skill state as policies allow
```

Physical output paths used by existing runtime concepts may coexist with this structure. The key invariant is ownership: files listed in `manifest.json` are managed by Wisk; files outside that set are consumer/runtime state and are never overwritten by `upgrade`.

Consumers are not expected to understand or maintain every managed file physically present under `.wisk/`. The useful measure of adoption complexity is the consumer-owned surface, not the generated file count.

Bootstrap also installs a managed `.wisk/.gitignore`. It ignores only reproducible managed state: the local `.gitignore` itself, `manifest.json`, `specs/`, and `knowledge/system/`. Consumer configuration in `knowledge/local/` and runtime-produced Experience, Wiki, and Skill state remain visible to Git. A clean consumer therefore does not acquire a large untracked diff merely by running `init`.

Versioned consumer/runtime knowledge is also safe across clones. If a fresh clone already contains files under `knowledge/local/`, `knowledge/experiences/`, `knowledge/wiki/`, or `knowledge/skills/`, `init` preserves those files byte-for-byte and installs the managed surface around them. Existing unmanaged files outside those namespaces are still refused rather than guessed at.

## Standard profile

The standard profile makes the canonical cycle useful without requiring a scheduler-specific prompt.

### Experience

Experience is normal work. It is available on explicit `start-next` invocation and has the lowest automatic priority of the three learning roles.

### Wiki

Wiki becomes eligible after three new Experiences since its previous run. It has higher priority than Experience so accumulated evidence is periodically synthesized.

### Skill

Skill becomes eligible after six new Experiences since its previous run. Wiki has higher priority than Skill. Therefore, when both thresholds are reached, Wiki runs first; on the next invocation Skill can act on fresh synthesis.

This yields a simple causal rhythm without adding a fourth evaluator or a new persistence metric:

```text
Experience × 3 → Wiki
Experience × 3 → Wiki → Skill
repeat
```

Consumers may replace these thresholds. They are a product default, not a universal law.

## Explicit start semantics

`session next` remains an explanation of automatically eligible work.

`session start-next` is itself an explicit request to do useful work. It considers on-demand eligibility in addition to automatic triggers. The standard profile marks only Experience as on-demand, so an invocation behaves as follows:

1. if Wiki or Skill is due, the higher-priority due session runs;
2. otherwise Experience starts;
3. a targeted Handoff may still make its compatible session eligible according to cadence policy.

This makes the short external prompt reliable without configuring an arbitrary clock interval merely to keep Experience selectable.

## Bootstrap

`wisk init <repository>` is non-destructive.

It:

1. refuses to overwrite an existing managed installation;
2. creates the minimum `.wisk/` structure;
3. installs normative specs, system profile files, and the managed Git ignore rules shipped with the installed Wisk version;
4. records SHA-256 hashes and format/runtime version in `manifest.json`;
5. validates the resulting bundle;
6. reports the canonical next command.

An existing unrelated `.wisk/` directory is not silently adopted. Migration of legacy/manual installations is a distinct operation because guessing ownership is unsafe. The safe exception is previously versioned consumer/runtime knowledge under `knowledge/local/`, `knowledge/experiences/`, `knowledge/wiki/`, and `knowledge/skills/`; those namespaces are explicitly outside the managed surface and are preserved during initialization.

## Upgrade

`wisk upgrade <repository>` updates only manifest-managed files.

Before writing anything it compares each managed file with the hash recorded by the previous installation. If a managed file was edited locally and the new version would replace it, upgrade reports a conflict and performs no partial upgrade.

When there are no conflicts, upgrade:

- refreshes managed files from the installed runtime;
- adds newly managed files;
- removes obsolete managed files only when they still match the previous recorded hash;
- leaves all consumer/runtime files untouched;
- validates a staged candidate before touching live state;
- restores the previous live state if the final write fails;
- writes a new manifest only after the managed update succeeds.

The first implementation intentionally has no force-overwrite mode. Resolving an ownership conflict should be explicit.

## Distribution assets

The wheel must carry the normative `specs/` and canonical role/RunSpec sources used by bootstrap. Source checkouts may read the repository copies directly, but installed consumers must not depend on the Wisk Git checkout being present.

The source repository remains the authority for canonical specs and role definitions; packaging should include those same files rather than maintaining divergent hand-copied versions.

## Local specialization

A consumer should specialize a managed role rather than fork it. SessionType inheritance is the primary mechanism:

```yaml
type: SessionType
id: session-types/judicial-experience
title: Judicial Experience
purpose: "Do substantive work in the Judicial repository."
extends: session-types/standard-experience
run_spec: run-specs/experience
nudges:
  - "Prefer substantive repository value over meta-work."
```

The scheduler treats inheritance as specialization. If a parent has a child, automatic and `start-next` selection consider the leaf specialization instead of making parent and child compete by priority or lexical order. The parent remains explicitly startable by id.

A consumer that needs one extra operational requirement should not copy the parent RunSpec. `parent_spec` appends the four required component lists into the effective contract:

```yaml
type: RunSpec
id: run-specs/judicial-skill
title: Judicial Skill evolution
version: "1.0.0"
status: active
parent_spec: run-specs/skill
required_reading_kinds: []
required_goal_kinds: []
required_evidence_kinds: []
required_check_kinds:
  - proportionality
```

The effective RunSpec inherits the canonical Skill readings, goal, evidence, lineage check, result states, and completion guidance while adding only `proportionality`. The complete effective contract is pinned into the LoopRun so later changes to either parent or child do not rewrite history.

Handoffs follow the same specialization semantics: a Handoff targeting a parent SessionType can make a compatible leaf specialization eligible. This lets generic producers hand work to a role without knowing every consumer-specific child.

The design goal is small local configuration. A consumer should only declare differences that carry domain meaning.

## Upgrade compatibility

The manifest has its own `format_version`, independent of the package semantic version. A future runtime that cannot understand an older manifest must fail with an actionable migration message rather than guessing.

## Success criterion

A new repository can adopt Wisk through `init`, immediately run `session start-next`, and receive the canonical learning behavior. A real consumer such as Judicial should then be able to delete most of its hand-built Wisk bootstrap and retain only domain specialization and learned state.

If a consumer must understand Wisk's package topology, manually synchronize core specs, accept generated managed files as repository noise, or lose learned state when cloning the repository, this RFC has not been satisfied.
