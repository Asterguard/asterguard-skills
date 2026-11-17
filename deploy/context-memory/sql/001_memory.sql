-- Long-lived memory plane — the team's durable security record.
-- Reused VERBATIM from the AsterVault memory backend (security/memory.py). The MCP server reads this
-- table unchanged; do not rename columns. Scope (tenant/team/app) is stamped by the server from the
-- authenticated identity, never from the caller's payload.

CREATE TABLE IF NOT EXISTS security_memory (
    id          TEXT PRIMARY KEY,
    tenant      TEXT NOT NULL,
    team        TEXT NOT NULL DEFAULT '',
    app         TEXT NOT NULL DEFAULT '',
    weakness_id TEXT NOT NULL DEFAULT '',
    topic       TEXT NOT NULL DEFAULT '',
    kind        TEXT NOT NULL,                 -- one of: decision | finding | fix | review | waiver
    promoted    BOOLEAN NOT NULL DEFAULT FALSE, -- review-gated: a one-off → an approved team pattern
    created_at  DOUBLE PRECISION NOT NULL,      -- epoch seconds (matches the backend contract)
    document    JSONB NOT NULL DEFAULT '{}'     -- the full record incl. the *why*
);

CREATE INDEX IF NOT EXISTS ix_security_memory_tenant      ON security_memory (tenant);
CREATE INDEX IF NOT EXISTS ix_security_memory_tenant_app  ON security_memory (tenant, app);
CREATE INDEX IF NOT EXISTS ix_security_memory_tenant_kind ON security_memory (tenant, kind);
CREATE INDEX IF NOT EXISTS ix_security_memory_weakness    ON security_memory (tenant, weakness_id);
CREATE INDEX IF NOT EXISTS ix_security_memory_promoted    ON security_memory (tenant, promoted);
