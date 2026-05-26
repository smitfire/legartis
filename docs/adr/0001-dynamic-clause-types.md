# 0001 — Dynamic clause types (taxonomy lives in the database)

**Status:** accepted

Clause types are now rows in a `clause_types` table with full CRUD, instead of a closed `StrEnum` + Postgres `CHECK` constraint. This reverses the original design recorded in the README (*"Clause types: Python StrEnum + DB CHECK, not a join table"*) and the CLAUDE.md anti-pattern (*"Don't model an entire taxonomy"*).

## Why we reversed it

`docs/ai-features.md` proposes an LLM that emits `LabelProposal` rows. The closed enum meant the LLM could only label sentences with one of the seven seeded categories — proposing a brand-new clause type would require a code change and a redeploy. Moving the taxonomy into a row store is the foundation that lets the AI extend the vocabulary at runtime; the human moderation surface (review queue, source provenance, approval status) lands on top of it later.

## Trade-offs we accepted

- **One extra JOIN** on the dashboard's filter/group queries, and on the `/clause-type-counts` aggregation. Performance impact is negligible at the case-study scale; an index on `labels.clause_type_id` covers it.
- **Cascade delete from `clause_types` to `labels`.** Deleting a type silently drops every label that referenced it — the alternative (block with 409) was rejected in favour of the simpler UX. The user makes the call when they hit the button.
- **Value field is immutable.** Only `label` (display name) is editable. The machine `value` is the wire identifier (`?type=governing_law`, `POST .../labels {clause_type: "..."}`) and renaming it would break bookmarked URLs and any in-flight AI proposals. Collisions on slug derivation are auto-suffixed (`force_majeure_2`, `_3`, …) so the UX never blocks the user.

## What stays the same

- The Pydantic wire format keeps `clause_type: str`. Existing API consumers see the same field shape; only the set of allowed values is now open.
- The seven seed values keep their hand-picked dashboard colours. New types fall back to a hashed palette.
- The aggregate is unchanged: `Sentence (1) → (N) Label (N) → (1) ClauseType`. No new ownership boundaries.
