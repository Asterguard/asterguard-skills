-- App / engagement CONTEXT plane — the folded current picture per target, shared across the team.
-- The local `./.asterguard/context.json` + `events.jsonl` are the offline mirror of these two tables;
-- the MCP server syncs the STRUCTURAL fold up (never raw code or data).

-- The folded current context for one engagement (one target: repo / image / live agent).
CREATE TABLE IF NOT EXISTS engagement_context (
    id               TEXT PRIMARY KEY,            -- engagement id
    tenant           TEXT NOT NULL,
    team             TEXT NOT NULL DEFAULT '',
    app              TEXT NOT NULL DEFAULT '',    -- the target identifier
    status           TEXT NOT NULL DEFAULT 'active',  -- active | paused | closed
    context          JSONB NOT NULL DEFAULT '{}', -- the fold: open findings, posture, controls, waivers, proven-breaks
    latest_graph_ref TEXT NOT NULL DEFAULT '',    -- pointer to the latest security graph artifact
    counters         JSONB NOT NULL DEFAULT '{}', -- run/finding counters
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_engagement_context_tenant     ON engagement_context (tenant);
CREATE UNIQUE INDEX IF NOT EXISTS ux_engagement_tenant_app  ON engagement_context (tenant, app);

-- The append-only structural event stream (the shared mirror of events.jsonl). The context above is a
-- reproducible fold of these rows, so it can always be rebuilt.
CREATE TABLE IF NOT EXISTS engagement_event (
    seq           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagement_context(id) ON DELETE CASCADE,
    tenant        TEXT NOT NULL,
    kind          TEXT NOT NULL,                 -- run_started|run_ended|scan_completed|finding_opened|
                                                 -- finding_closed|test_run|canary_hit|verdict|decision|
                                                 -- waiver|policy_recommended|policy_applied|gate_verdict|note
    run_id        TEXT NOT NULL DEFAULT '',
    actor         TEXT NOT NULL DEFAULT '',
    harness       TEXT NOT NULL DEFAULT '',      -- claude | codex | cursor | opencode | deepseek | ...
    commit_sha    TEXT NOT NULL DEFAULT '',
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    document      JSONB NOT NULL DEFAULT '{}'    -- the typed event payload (structural only)
);

CREATE INDEX IF NOT EXISTS ix_engagement_event_eng   ON engagement_event (engagement_id, ts);
CREATE INDEX IF NOT EXISTS ix_engagement_event_scope ON engagement_event (tenant, kind, ts);
CREATE INDEX IF NOT EXISTS ix_engagement_event_run   ON engagement_event (engagement_id, run_id);
