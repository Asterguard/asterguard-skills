-- Short-lived (working) memory plane — a run's scratch + cross-skill handoff, scoped to one run and
-- expired by TTL. Keeps durable memory (security_memory) clean: in-flight state never lands there.

CREATE TABLE IF NOT EXISTS working_memory (
    id            TEXT PRIMARY KEY,              -- uuid, or a deterministic (scope,key) hash
    tenant        TEXT NOT NULL,
    team          TEXT NOT NULL DEFAULT '',
    engagement_id TEXT NOT NULL DEFAULT '',
    run_id        TEXT NOT NULL DEFAULT '',
    key           TEXT NOT NULL,                 -- e.g. 'stage:enrich-indicator:LLM01', 'cache:graph.enrich:svc:x'
    value         JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at    TIMESTAMPTZ NOT NULL,          -- set by the writer (default TTL, e.g. now() + interval '2 hours')
    CONSTRAINT ux_working_memory_scope UNIQUE (tenant, engagement_id, run_id, key)
);

CREATE INDEX IF NOT EXISTS ix_working_memory_expiry ON working_memory (expires_at);
CREATE INDEX IF NOT EXISTS ix_working_memory_run    ON working_memory (tenant, run_id);

-- Sweep expired rows. Call from pg_cron, a sidecar, or the MCP server's own timer:
--   SELECT purge_expired_working_memory();
CREATE OR REPLACE FUNCTION purge_expired_working_memory() RETURNS integer AS $$
DECLARE
    deleted integer;
BEGIN
    DELETE FROM working_memory WHERE expires_at < now();
    GET DIAGNOSTICS deleted = ROW_COUNT;
    RETURN deleted;
END;
$$ LANGUAGE plpgsql;

-- If pg_cron is available, schedule a sweep every 15 minutes (safe to leave commented out otherwise):
-- SELECT cron.schedule('purge-working-memory', '*/15 * * * *', 'SELECT purge_expired_working_memory();');
