---
title: "RFC 0007 — Work traces as the Raw Layer and the 0.4 RC learning pivot"
status: proposed
created: 2026-09-08
target_release: "0.4.0rc1"
supersedes:
  - "RFC 0004: Experience as the canonical execution role and separate Experience artifacts"
---

# RFC 0007 — Work traces as the Raw Layer and the 0.4 RC learning pivot

## Summary

Wisk should pivot its canonical learning model before declaring `0.4.0` stable.

The key change is conceptual but has direct runtime and schema consequences:

> **The raw experience of an agent is the persisted execution trace of its work, not a second artifact produced after the run.**

A real work session is a `LoopRun` classified by a `SessionType`. The run and its typed child records preserve what happened while the agent still has the execution context. A later Wiki Maintainer studies a corpus of those Work runs and compiles them into durable `WikiEntry` knowledge. A Skill Evolver then uses the Wiki, selected raw traces, current skills, and prior proposal outcomes to propose or revise executable skills.

The canonical learning loop becomes:

```text
Worker
  │ performs useful external work using available skills
  ▼
Work LoopRun + typed Run* records       ← Raw Layer
  │
  ▼
Wiki Maintainer
  │ compares multiple Work runs
  ▼
WikiEntry                               ← Wiki Layer
  │
  ▼
Skill Evolver
  │ proposes an atomic procedural intervention
  ▼
SkillProposal → experimental AgentSkill
  │
  ▼
validation / gating / rollback
  │
  └──────────────► later Worker runs record the skill/version actually exercised
```

This RFC therefore renames the canonical execution role from **Experience** to **Work**, treats the closed Work `LoopRun` graph as Wisk's Raw Layer, deprecates a separate canonical `Experience` document, adds explicit execution observations and skill-use provenance, narrows Wiki sessions to synthesis rather than operational continuation, and makes the complete Work → Wiki → Skill → Work loop the release criterion for `0.4.0` final.

The breaking model should first ship as **`0.4.0rc1`** and be dogfooded in a real consumer before final release.

## Motivation

### Wisk exists to persist what ordinary agent runtimes lose

A normal coding/research/newsroom/legal agent may do useful work and retain rich local context while a session is alive: what it tried, which alternative it rejected, where it lost time, which tool or skill helped, which assumption failed, what was easy, what surprised it, and what evidence changed its plan.

Without an explicit runtime contract, much of that operational context remains ephemeral in the model/provider session. It is not deposited in the repository as structured data that a later independent agent can study.

Wisk's distinctive job is to make that execution history persistent and queryable:

```text
task
→ agent works
→ typed execution facts are persisted while context is hot
→ run closes
→ later agents can inspect the corpus
→ wiki knowledge compounds
→ procedural skills evolve from that knowledge
```

`LoopRun` is therefore not administrative scaffolding around the real artifact. A closed run plus its typed components **is the repository-resident execution trace**.

### The WikiSkill paper supports this separation

Wisk is inspired by Google Research's **“WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution”** by Liyan Tang, Cyrus Rashtchian, Chun-Sung Ferng, Andrew Tomkins, Da-Cheng Juan, and Tu Vu (2026):

https://arxiv.org/abs/2608.27454

The paper separates the workspace into three layers (§3.1):

1. **Raw Layer** — immutable execution traces;
2. **Wiki Layer** — structured, persistent, compounding knowledge;
3. **Skills Layer** — evolving executable procedural guidance.

Its orchestration (§3.2) likewise separates four responsibilities:

1. an Inference Agent executes tasks using active skills and emits traces;
2. a Wiki Maintainer analyzes sampled successful and failing traces and updates persistent knowledge;
3. a Skill Proposer reads the Wiki, skill-impact history, current skills, and selected traces to propose an atomic skill change;
4. gating/rollback accepts or rejects the intervention while the Wiki persists regardless of outcome.

Two paper properties are especially important for Wisk:

- the execution agent is **restricted from Wiki access** during training rollouts; the Wiki is synthesis context, not ordinary task context;
- the history of proposed skill changes and their objective acceptance/rejection outcome remains available so future proposers do not repeat failed interventions.

Wisk need not reproduce the paper's benchmark harness literally. It should preserve the architectural separation that makes accumulated knowledge useful.

### The CausaGanha dogfood validates the first half of the model

The repository `franklinbaldo/causaganha` has already run a prompt-driven predecessor of this architecture and then migrated recent rounds onto Wisk. The results provide stronger design evidence than schema aesthetics alone.

Several real merged PR chains show execution history compounding across independent rounds:

- **#1323 → #1325 → #1328**: one Work round found drift between Python and DuckDB-SQL normalization; a later round used the recorded deferral and repeated evidence to justify extracting a shared rule; a subsequent round found that the extraction itself introduced a `NULL` vs `""` regression and that the parity test masked the bug. The system corrected its own prior improvement rather than treating previous output as authoritative.
- **#1332**: a prior run left a plausible calendar-day bug as a future lead but explicitly recorded uncertainty about whether the code was live. The later run traced callers, found the entire surface dead, and correctly deleted it instead of repairing unreachable behavior. Prior `next_move` text functioned as research material, not an instruction to obey.
- **#1334 → #1335**: the Work round found and fixed another duplicated DJEN-classification bug and recorded a near-miss where an attempted test write would have overwritten unrelated coverage. The following Wiki round consolidated the episode as the sixth confirmed instance of the same broader drift pattern and refined the persistent Wiki accordingly.

These are exactly the desirable properties of persistent learning:

- a later run can verify, reject, or refine an earlier run's interpretation;
- repeated episodes can become durable knowledge;
- durable knowledge can change future investigation strategy;
- mistakes in the learning process itself remain available as future evidence.

The dogfood also exposes a gap: the repository has exercised **Work → Wiki** repeatedly, but it has not yet exercised a meaningful **Wiki → Skill → later Work using that skill** cycle. `0.4.0` should not be called stable until that leg works end-to-end.

## Decision 1 — Canonical roles are Work, Wiki, and Skill

RFC 0004 named the canonical roles Experience / Wiki / Skill. The responsibilities were mostly correct, but `Experience` conflates a role with the trace produced by the role.

The canonical roles become:

- `session-types/work` — human-facing role: **Worker**;
- `session-types/wiki` — human-facing role: **Wiki Maintainer**;
- `session-types/skill` — human-facing role: **Skill Evolver**.

Consumer repositories normally specialize these parent roles.

Examples of Work specializations include software development, investigation, newsroom reporting, legal drafting, research, data engineering, and design work. They are Work because their primary purpose is to change or inspect the external project while recording what happened.

The canonical vocabulary deliberately distinguishes **role** from **artifact**:

```text
role: Worker
artifact: Work LoopRun trace

role: Wiki Maintainer
artifact: WikiEntry updates

role: Skill Evolver
artifact: SkillProposal / AgentSkill lifecycle changes
```

Compatibility aliases may preserve `experience` / `standard-experience` during the RC migration window, but new bundles and documentation should teach Work / Wiki / Skill.

## Decision 2 — A closed Work LoopRun graph is the Raw Layer

Wisk should not require a second canonical `Experience` document that restates what a run already records.

The Raw Layer is the queryable graph rooted at a Work `LoopRun`:

```text
LoopRun
├── RunReading*
├── RunGoal*
├── RunDecision*
├── RunEvidence*
├── RunCheck*
├── RunObservation*
├── RunSkillUse*
└── RunOutcome
```

The parent remains intentionally small. Child records carry `run` back-references, so lists of child identifiers on `LoopRun` are derived membership and must not be maintained as a second source of truth.

This preserves the useful direction already taken by the schema-simplification work in PR #70: remove redundant membership backlinks while retaining semantic lineage.

### Membership is derivable; meaning is not

The migration uses this rule:

> A link that only means “this record belongs to this run” should exist once, on the child that owns the relationship. A link that expresses lineage, causal selection, verification, derivation, or evaluation remains explicit.

Examples:

- `RunCheck.run` is sufficient; `LoopRun.checks` is redundant;
- `SkillProposal.run` is sufficient; `LoopRun.proposals_generated` is redundant;
- `RunCheck.evidence` remains because it means “this verification rests on this evidence”, not merely “both belong to the same run”;
- `WikiEntry.evidence` remains because it identifies which raw episodes support durable knowledge;
- `AgentSkill.derived_from` remains because it maps executable procedure back to the Wiki knowledge that motivated it, analogous to WikiSkill's `PURPOSE.md`;
- `SkillProposal.based_on` and proposal/gating history remain because rejected interventions are part of the learning state.

## Decision 3 — Work runs must preserve execution metadata while context is hot

The Worker should not be asked to author a mini academic paper about itself. It should preserve local, factual, execution-adjacent metadata that a later Wiki Maintainer cannot reconstruct reliably after the session ends.

The runtime should make the following facts explicit and queryable.

### Timing

`LoopRun` gains canonical execution timestamps:

- `started_at: TIMESTAMPTZ`;
- `finished_at: TIMESTAMPTZ | null`.

Duration is derived from timestamps; the model should not estimate it.

The old generic `timestamp` should migrate toward the explicit lifecycle pair.

### Goal and result

`RunGoal` and `RunOutcome` remain the authoritative typed representation for what the run attempted and what state it reached.

A goal should preserve an observable `success_signal`. Outcome should remain small — result state, work status, summary, continuation — rather than copy all run children back into a second list.

### Decisions and verification

`RunDecision` records explicit choices that matter for later interpretation. `RunEvidence` records observed support. `RunCheck` records the procedure used to verify a claim.

A required check kind is satisfied only by the standing/latest check of that kind when its status is `pass`. A failed or inconclusive check must never satisfy a closure contract merely because a record exists.

### Observations

Wisk adds `RunObservation` for locally important facts that are neither a goal, a formal decision, nor verification evidence.

The initial stable `kind` vocabulary should be intentionally small:

- `friction` — something was unexpectedly difficult or expensive;
- `surprise` — observed behavior contradicted the working expectation;
- `near_miss` — an error was nearly introduced or propagated but was caught;
- `workaround` — progress required a non-obvious workaround or structural compromise;
- `opportunity` — a relevant lead was discovered but not selected or fully investigated;
- `skill_feedback` — local evidence about the usefulness or harm of procedural guidance.

The record should minimally support:

```yaml
type: RunObservation
id: run-observations/...
run: runs/...
kind: near_miss
summary: "The first test-file write would have overwritten unrelated coverage; git diff caught it before commit."
impact: high
observed_at: 2026-09-08T17:30:00Z
```

`kind` is extensible by consumer profiles. Wisk core should not hard-code domain-specific taxonomies.

The purpose is not sentiment. It is to preserve execution texture useful for later synthesis: what hurt, what helped, what surprised the Worker, and what should be compared against other episodes.

## Decision 4 — Skill use is explicit run provenance

The Raw Layer must answer which procedure actually guided a Work run.

The old `Experience.skill_used` / `Experience.skill_version` semantics move to a run-scoped record rather than disappear with `Experience`.

Wisk adds `RunSkillUse` with at least:

- `run`;
- `skill`;
- `skill_version`;
- whether the version was active/incumbent or experimental/candidate when exercised;
- optional applicability/use notes.

Local assessment belongs either on the record or in a `RunObservation(kind: skill_feedback)` linked to it. The important invariant is objective provenance first: a Wiki/Skill session must be able to query all Work runs that exercised a given skill version.

A later Skill Evolver should be able to ask:

```text
Which Work runs exercised skill X@1.4.0?
Which exercised candidate X@1.5.0rc1?
What goals and outcomes did those runs have?
What recurring friction/near-miss observations differ between variants?
What Wiki entries synthesize those episodes?
```

## Decision 5 — Context policy follows cognitive role

`SessionType` is not merely a scheduling label. It identifies what cognitive job the agent is performing and therefore what context it should normally receive.

### Worker

A Work session:

- receives the real task/repository context;
- receives applicable active or deliberately experimental skills;
- may receive compatible handoff context;
- records the raw execution trace;
- **does not receive the Wiki as ordinary working context by default**;
- does not create or revise Wiki knowledge merely because it noticed a pattern;
- does not globally promote/reject a skill based on one successful or failing episode.

This matches the WikiSkill finding that letting the execution agent read the Wiki during training harmed skill development. Wisk may allow consumer overrides, but the standard profile should encode Wiki as off-limits to Worker sessions.

### Wiki Maintainer

A Wiki session:

- reads a selected corpus of closed Work runs, including success and failure;
- reads existing Wiki knowledge;
- performs root-cause analysis, comparison, contradiction handling, and pattern consolidation;
- creates or incrementally updates `WikiEntry` records;
- preserves evidence/lineage to the Work runs that support the synthesis;
- does **not** do ordinary product work merely because a handoff or PR is pending;
- does not change executable skills.

The Wiki Maintainer may conclude that no durable update is justified. “No change” is a valid outcome when episodes are isolated or contradictory.

### Skill Evolver

A Skill session:

- reads Wiki knowledge and its lineage;
- reads current skills;
- reads prior `SkillProposal` / validation / acceptance history;
- inspects selected raw Work traces when necessary;
- creates one atomic proposal targeting one skill at a time;
- may materialize a candidate `AgentSkill` as `experimental`;
- does not treat proposal creation as promotion.

## Decision 6 — Handoff continuation and Wiki synthesis are orthogonal

Recent dogfood sometimes selected a Wiki run because an awaiting-CI handoff existed, then merged the PR and updated the Wiki in the same session. That is useful output but muddles roles.

A handoff answers:

> What operational responsibility was transferred from a previous execution?

A `SessionType` answers:

> What cognitive role is this agent exercising now?

These are orthogonal dimensions.

Resolving CI, updating a branch, merging a PR, validating live repository state, or finishing operational work is normally **Work**, even when the result later deserves Wiki synthesis.

A later Wiki run may study that episode on its own cadence and decide whether it adds durable knowledge.

`wisk start` therefore must not treat “active handoff exists” as a reason to select the Wiki role. Handoff compatibility participates in Work/session selection; Wiki cadence/eligibility is driven by synthesis policy.

## Decision 7 — Wiki synthesis is corpus-based, not one-run shadowing

The target lifecycle is not:

```text
Work → immediate Wiki → immediate Skill
```

Instead, Work runs accumulate. Wiki cadence samples enough relevant episodes to justify comparison and consolidation. Skill cadence acts when Wiki knowledge and proposal history justify a procedural intervention.

```text
Work   Work   Work   Work
  \      |      |      /
        Wiki
          │
       more Work
          │
        Wiki
          │
        Skill
```

This matters because durable knowledge is often the result of recurrence, contrast, or contradiction across episodes. The CausaGanha chain #1323 → #1325 is a concrete example: the first occurrence justified a fix and a deferred opportunity; repeated evidence later justified extraction.

The scheduler may use count thresholds, elapsed time, changed knowledge, explicit request, or other consumer policy. Wisk core should expose the ingredients and role boundaries rather than impose one universal cadence.

## Decision 8 — Skill proposals retain objective intervention history

PR #70's direction for `SkillProposal` is retained and becomes part of this RFC's complete learning loop.

A proposal must preserve enough information to reconstruct:

- the target skill/version;
- the motivating Wiki knowledge / traces;
- the candidate skill/version;
- the atomic change attempted;
- validation evidence;
- acceptance or rejection;
- decision time and rationale.

Rejected proposals are durable learning state, not garbage to delete. This is Wisk's typed counterpart to WikiSkill's `skill-impact.md` history.

`SkillEvaluation` remains an optional detailed artifact when a consumer needs it. It is not a mandatory fourth canonical session role.

Gating may be implemented by CI, benchmark harness, explicit validation Work runs, or a consumer-specific evaluator. The invariant is semantic: a candidate does not silently become active merely because a Skill Evolver proposed it.

## Decision 9 — `0.4` ships as a release candidate first

The open schema-simplification work should not publish directly as stable `0.4.0` while the canonical pipeline is changing at the same time.

The first release under the new model is:

```text
0.4.0rc1
```

The RC intentionally allows breaking migration while preserving a clear point at which consumer bundles can dogfood the new model.

The `0.4.0rc1` scope includes:

1. the one-source-of-truth schema simplification from PR #70;
2. passing-status semantics for required checks;
3. typed SkillProposal gating/proposal history;
4. canonical Work / Wiki / Skill vocabulary and compatibility aliases;
5. Work `LoopRun` as the Raw Layer;
6. deprecation/migration path for canonical `Experience` documents;
7. `RunObservation`;
8. explicit run timestamps;
9. explicit skill/version provenance through `RunSkillUse` or an equivalent run-scoped contract;
10. standard context policies separating Worker from Wiki;
11. scheduler semantics that do not conflate handoff continuation with Wiki synthesis;
12. migrations and conformance tests for existing consumer bundles.

The exact internal schema can evolve during the RC if real dogfood exposes a better representation. That is the purpose of the pre-release.

## CausaGanha as the 0.4 golden corpus

`franklinbaldo/causaganha` should be the first external consumer used to validate the RC because it already contains both the predecessor `AgentRun` model and the Wisk `LoopRun` model, plus a dense sequence of independently useful agent rounds.

The migration should prove that the new model can represent the information that mattered in the old prototype without restoring a monolithic run document.

The older `AgentRun` prototype usefully preserved fields such as:

- start/completion time;
- repository baseline;
- considered work;
- selected work;
- expected behavior;
- primary goal;
- decisions, evidence, checks, outcome, and continuation.

The RC should preserve the important semantics through smaller typed records:

- lifecycle timing on `LoopRun`;
- goals through `RunGoal`;
- selected alternatives through `RunDecision`;
- discarded/deferred but important leads through `RunObservation(kind: opportunity)`;
- verification through `RunCheck`;
- execution result through `RunOutcome`;
- repository/environment continuation provenance through the handoff/revalidation contract from RFC 0006;
- skill provenance through `RunSkillUse`.

The test is not whether every old field survives by name. The test is whether a later Wiki Maintainer can answer the useful historical questions without reading opaque provider chat history.

## Required dogfood experiment before 0.4.0 final

The CausaGanha Wiki already contains a strong candidate for the first complete Wiki → Skill experiment: repeated drift caused by duplicated domain classification/normalization logic.

A Skill run should be able to turn the accumulated Wiki knowledge into a proposal roughly equivalent to this procedure:

```text
When a bug changes classification/normalization semantics:
1. identify the canonical rule;
2. enumerate all callers and local reimplementations;
3. include ops scripts and diagnostic tools, not only production paths;
4. reproduce divergence with RED evidence before repair;
5. when runtimes prevent direct code sharing, share the rule's constants/contract
   and add a cross-runtime parity test;
6. record remaining structurally duplicated paths for later Work/Wiki comparison.
```

The candidate must then be gated and exercised by at least one later Work run with the actual skill/version recorded. That later trace must be available to a Wiki session for comparison.

This closes the leg that current dogfood has not yet tested.

## Promotion criteria: rc1 → 0.4.0

`0.4.0` stable may be cut only when all of the following are demonstrated.

### Runtime/model

1. a Work `LoopRun` can be reconstructed/queryed with goals, evidence, checks, observations, skill uses, and outcome without membership lists on the parent;
2. failed/inconclusive standing required checks keep the run open;
3. `started_at` / `finished_at` provide objective duration;
4. the standard Worker context policy does not inject Wiki knowledge;
5. the Wiki Maintainer can select/read closed Work traces and ground `WikiEntry` updates in them;
6. the Skill Evolver can read Wiki lineage, current skills, prior proposal outcomes, and selected traces;
7. an experimental skill version can be tied to the Work runs that actually exercised it;
8. rejected skill proposals remain inspectable and prevent blind repetition of failed interventions;
9. handoff continuation does not force Wiki role selection.

### Migration

10. an existing `0.3.x` consumer bundle can be inspected and migrated with `wisk migrate` / `--apply` rather than failing opaquely;
11. canonical `experience` SessionTypes/RunSpecs have a documented compatibility/migration path to `work`;
12. no important skill-version provenance is lost when separate `Experience` artifacts are deprecated;
13. the migrated CausaGanha knowledge bundle is normatively conformant.

### Complete learning loop

14. CausaGanha completes at least one real **Work → Wiki → SkillProposal → gating → later Work** chain under the RC;
15. the later Work run records the exact candidate/incumbent skill version exercised;
16. a subsequent Wiki read can compare that episode with prior raw traces without relying on provider conversation history;
17. the resulting lineage answers: what motivated the skill change, what was proposed, how it was gated, which run exercised it, what happened, and what durable knowledge changed afterward.

The final criterion is the architectural acceptance test for Wisk 0.4.

## Migration from RFC 0004

RFC 0004 remains useful for its separation of observation, synthesis, intervention, and optional evaluation artifacts. This RFC supersedes the following parts:

- canonical execution role name `Experience` → `Work`;
- separate canonical `Experience` artifact → Work `LoopRun` graph as the Raw Layer;
- `Experience.skill_used` / `skill_version` → run-scoped skill-use provenance;
- any implication that operational handoff continuation belongs inside a Wiki session.

The following RFC 0004 decisions remain:

- Wiki owns synthesis rather than one-run judgment;
- Skill owns procedural intervention/lifecycle decisions;
- candidate creation and promotion are distinct moments;
- `SkillEvaluation` is optional and not a mandatory fourth canonical role;
- semantic lineage across raw evidence, Wiki knowledge, proposals, and skills is required.

## Compatibility strategy

During the RC:

- `session-types/experience` may resolve as a deprecated alias/parent compatibility bridge to `session-types/work`;
- `run-specs/experience` may resolve to or migrate toward `run-specs/work`;
- read support for old `Experience` documents may remain for migration/query purposes;
- new standard-profile output must not create separate Experience artifacts;
- CLI/MCP should emit deprecation guidance when explicit old canonical names are selected;
- migration should preserve authored IDs and lineage where possible rather than silently rewriting unrelated consumer concepts.

Compatibility is a bridge, not a reason to keep two canonical models indefinitely.

## Non-goals

This RFC does not require:

- storing private chain-of-thought; Wisk should persist observable actions, outputs, explicit decisions, structured observations, and other safe execution facts rather than depend on hidden reasoning traces;
- a universal Worker observation taxonomy beyond the small core kinds;
- a fixed Work/Wiki/Skill cadence for every consumer;
- a mandatory A/B allocation algorithm for incumbent vs candidate skill versions;
- benchmark-score gating as the only valid gating mechanism;
- a dedicated fourth evaluator SessionType;
- automatic skill promotion after one successful Work run;
- immediate Wiki synthesis after every Work run;
- forcing every consumer to use Git-specific repository metadata as generic Run fields.

## Consequences

### Positive

Wisk's object model becomes easier to explain:

> **Wisk turns agent work into persistent operational memory, compiles repeated experience into Wiki knowledge, and evolves executable skills from that knowledge.**

The model avoids a redundant Experience layer, preserves the execution facts a later synthesizer actually needs, and makes the repository — not the provider session — the durable learning substrate.

The CausaGanha evidence suggests the approach supports something stronger than memory: later independent executions can challenge, correct, or refine prior interpretations.

### Costs

`0.4` becomes a real breaking migration rather than a small schema cleanup. Standard profile names, docs, context policy, migration code, schemas, and consumer fixtures will change together.

The Raw Layer will also create more small records (`RunObservation`, `RunSkillUse`). This is intentional: queryable typed execution facts are more useful to later synthesis than one increasingly large prose outcome.

### Risk

The largest risk is over-modeling observations before dogfood teaches us which fields matter. The RC should therefore keep `RunObservation` compact and extensible, and use CausaGanha to decide whether further specialization is justified.

## Implementation sequence

The recommended implementation order is:

1. merge/retain PR #70's noncontroversial one-source-of-truth and standing-check fixes;
2. change the release target from `0.4.0` to `0.4.0rc1`;
3. add this RFC and mark the affected RFC 0004 semantics superseded;
4. add Work canonical SessionType/RunSpec plus compatibility aliases;
5. add explicit run lifecycle timestamps;
6. add `RunObservation` and `RunSkillUse` schemas/specs/runtime operations;
7. stop generating new separate `Experience` artifacts in the standard profile and migrate provenance to Work runs;
8. encode standard context policies for Worker, Wiki Maintainer, and Skill Evolver;
9. separate handoff-driven Work selection from Wiki cadence;
10. update migration logic and standard-profile bootstrap/upgrade;
11. migrate/dogfood CausaGanha under the RC;
12. run the first real Wiki → Skill proposal/gating → later Work experiment;
13. fix the model from dogfood evidence as needed and cut additional RCs;
14. release `0.4.0` only after the promotion criteria above are satisfied.

## Decision statement

Wisk `0.4` is not merely a schema simplification release. It is the release where the runtime's persistent-learning model becomes explicit:

```text
Work trace is Raw.
Wiki compiles Raw into knowledge.
Skill evolves procedure from knowledge.
Future Work records whether the procedure actually helped.
```

The project should publish this model first as `0.4.0rc1`, validate it against the CausaGanha corpus and a complete skill-evolution cycle, then promote it to stable `0.4.0`.