CREATE TABLE "RunSpec" (
    "id" VARCHAR,
    "title" VARCHAR,
    "version" VARCHAR,
    "status" VARCHAR,
    "required_reading_kinds" VARCHAR[],
    "required_goal_kinds" VARCHAR[],
    "required_evidence_kinds" VARCHAR[],
    "required_check_kinds" VARCHAR[],
    "skill" VARCHAR,
    "parent_spec" VARCHAR,
    "allowed_result_states" VARCHAR[],
    "completion_notes" VARCHAR
);
