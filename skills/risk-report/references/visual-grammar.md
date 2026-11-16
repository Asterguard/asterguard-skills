# Visual grammar — shared across every view

One visual language so every renderer (the attack-path graph, the BOM view, the console) means the same
thing. This is presentation (client-side); it carries no proprietary knowledge, only how to *draw* the
standardized data. All views read the same `graph.enrich` / `risk.score` JSON.

## Node color = what it is

| Appearance | Kinds | Meaning |
|---|---|---|
| **Red fill** (◆) | `untrusted`, `pii` (regulated store/field), `recipient` (external sink) | danger — untrusted source or regulated data or an exit |
| **Blue outline** (☻ ▣ ✉ ▤) | `identity`/`role`, `agent`, `tool`, `service` | an actor or capability on the path |

Icons: `untrusted/pii/recipient` → ◆ · `identity` → ☻ · `agent` → ▣ · `tool` → ✉ · `service` → ▤.

## Edge = relationship + path membership

- **Red solid, arrowhead** — the edge is **on the proven/violating path** (`onPath: true`, from a flow's `path_labels`).
- **Gray dashed** — structural/context edge (acts-as, runs-on) not on the violating path.
- Edge label = the `rel` (`instructs`, `reads`, `can call`, `content`, `sends to`, `acts as`, `runs on`).

## Badges & chips come from the data

- **`proven`** badge (red) — a `canary.verify → fired` hit or a broke behavioral test on this path. Else omit (or `theoretical`).
- **data-class** badge (`PII`/`PCI`/`PHI`) — from the flow's `data_classes`.
- **Control chips** — one per control on the path, status driven by the flow's `missing_control` + control state:
  `failing` (red) · `unverified` (amber) · `passing` (green).
- **ARS pill** — `risk.score` band color: `critical` red · `high` amber · `medium` lime · `low` green.

## The render-model (map `graph.enrich` → this)

Renderers consume a normalized model; `risk-report` maps the enrich/score JSON into it:

```jsonc
{
  "title": "…", "meta": { "paths": 1, "proven": 1, "source": "graph.enrich", "ars": 9.2, "band": "critical" },
  "nodes":  [ { "id", "label", "sub", "kind" } ],                 // kind drives color+icon
  "edges":  [ { "from", "to", "label", "onPath" } ],             // onPath drives red vs dashed
  "path":   { "label": "src → sink", "badges": [ { "text", "tone": "proven|pii|info" } ] },
  "evidence": "how it was proven",
  "controls": [ { "name", "status": "failing|unverified|passing" } ]
}
```

Layout is computed, not hand-placed: layer nodes by longest-path distance from a source (sources left,
sinks right), stack within a layer, route edges between. See `templates/attack-path.html`.
