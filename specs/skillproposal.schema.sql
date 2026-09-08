CREATE TABLE "SkillProposal" (
    "id" VARCHAR,
    "title" VARCHAR,
    "target_skill" VARCHAR,
    "target_version" VARCHAR,
    "status" VARCHAR,
    "motivation" VARCHAR,
    "based_on" VARCHAR[],
    "run" VARCHAR,
    "candidate_skill" VARCHAR,
    "candidate_version" VARCHAR,
    "validation" VARCHAR,
    "decided_at" TIMESTAMPTZ,
    "decision_rationale" VARCHAR
);
