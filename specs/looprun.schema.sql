CREATE TABLE "LoopRun" (
    "id" VARCHAR,
    "title" VARCHAR,
    "timestamp" TIMESTAMPTZ,
    "status" VARCHAR,
    "run_spec" VARCHAR,
    "run_spec_version" VARCHAR,
    "run_spec_digest" VARCHAR,
    "run_spec_snapshot" VARCHAR,
    "session_type" VARCHAR,
    "task" VARCHAR,
    "resumed_handoff" VARCHAR
);
