# Context & Memory data layer (the team tier)

The AsterGuard skills are **local-first**: every run reads and writes `./.asterguard/` plain files, so a
single engineer works fully offline. This directory is what a **growing team** stands up to make that
context and memory **shared, durable, and semantically searchable** across people, harnesses, and boxes
— without each person re-discovering the same app.

**We provide the MCP server.** You provide (or we host for you) the **stores** it reads. This folder is
the open, portable **contract** for those stores — the SQL schema, the Qdrant collection formats, and a
one-command `docker compose` to bring them up. Create them wherever you like (a managed Postgres +
Qdrant, your own cluster, or this compose); nothing here is tied to a specific box.

```
   skills (local-first)            AsterVault MCP server (we provide)         these stores (you own)
   engagement / memory-capture ──▶  memory.* · context.* · scratch.*  ──▶  Postgres  +  Qdrant
   knowledge-recall                 (authn → scope → audit)                 (this folder's schema)
        │                                                                        ▲
        └── offline: ./.asterguard/ files only ──────────────────────────────────┘ (no stores needed)
```

The server stamps the **tenant/team scope from the authenticated identity** — never from the caller —
so one team can never read or write another's rows. These tables simply carry the scope columns.

## The three planes

| Plane | What it holds | Lifetime | Store | File |
|---|---|---|---|---|
| **Long-lived memory** | the team's durable record — `decision`, `finding`, `fix`, `review`, `waiver` (each with the *why*), promoted patterns | permanent | Postgres `security_memory` | [`sql/001_memory.sql`](sql/001_memory.sql) |
| **App / engagement context** | the folded current picture per target (open findings, posture, controls, waivers, latest-graph pointer) + the shared structural event stream | durable | Postgres `engagement_context`, `engagement_event` | [`sql/002_context.sql`](sql/002_context.sql) |
| **Short-lived memory** | a run's working set — scratch, cross-skill/stage handoff, in-flight hypotheses, a grounding-result cache — scoped to `(tenant, engagement, run)` | **TTL'd** (`expires_at`) | Postgres `working_memory` | [`sql/003_working_memory.sql`](sql/003_working_memory.sql) |
| **Semantic recall** | vector embeddings of memory + context docs, so `knowledge-recall` finds "last time this app touched PII…" by meaning, not keyword | mirrors memory | Qdrant `security_memory` collection | [`qdrant/collections.json`](qdrant/collections.json) |

`security_memory` is reused **verbatim** from the AsterVault memory backend (`memory.py`) — the server
reads it unchanged. `engagement_context` and `working_memory` are the two additions that make context
and short-lived memory first-class and team-shared.

## Quick start (demo / self-host)

```bash
cp .env.example .env            # edit POSTGRES_PASSWORD and the embedding dim
docker compose up -d            # Postgres (applies sql/*.sql on first init) + Qdrant (collections created)
```

Then point the AsterVault MCP server at them:

```bash
export ASTERVAULT_DATABASE_URL="postgresql://asterguard:<pw>@<host>:5432/asterguard"
export ASTERVAULT_PACKS_QDRANT_URL="http://<host>:6333"   # same Qdrant; memory collection lives here
```

Or **create the objects wherever you already run Postgres/Qdrant** — the SQL and the collection JSON are
the whole contract; apply `sql/*.sql` to your database and `qdrant/create-collections.sh` (or the JSON)
to your Qdrant. No box required.

## Context & memory management — how it behaves

- **Context management.** The engagement's folded context lives in `engagement_context.context`
  (rebuildable from `engagement_event`). Any teammate or harness `open`s the same engagement and resumes
  the *same* picture. The local `./.asterguard/context.json` is the offline mirror; the server syncs the
  **structural** fold up (never raw code or data).
- **Memory management.** `memory-capture` writes a `security_memory` row (kind + the *why*); a review-gated
  `promote` flips `promoted` so a one-off becomes an approved team pattern. `knowledge-recall` reads both
  the rows (by scope) and the Qdrant vectors (by meaning).
- **Short-lived memory.** Within one run, skills stash working state in `working_memory` with a TTL, so a
  multi-step playbook (triage → enrich → investigate) hands off without bloating the model context or
  polluting durable memory. Expired rows are swept (`purge_expired_working_memory()` — call it from
  `pg_cron`, a sidecar, or the server's own timer).

## Tenant isolation & governance

Every table carries `tenant` (+ `team`, `app`). The MCP server derives the scope from the authenticated
identity and filters every read/write by it; it also routes each call through its audit log. Enable the
optional [`sql/010_row_security.sql.example`](sql/010_row_security.sql.example) (rename to drop
`.example`) if you want Postgres RLS as defense-in-depth.

## What is **not** here (by design)

- **The MCP server** — we provide it; it is the only component that talks to these stores on the skills'
  behalf.
- **The proprietary knowledge catalog** (ATT&CK / CAPEC / CWE / control crosswalk vector collections) —
  that is vendor-maintained and never shipped; these team stores hold **your** context and memory only.
- **The behavioral red-team** — part of the enterprise delivery.

See [`../../docs/MCP_WIRING.md`](../../docs/MCP_WIRING.md) for the full gateway wiring and the
SQLite-vs-Postgres single-node option.
