# CLAUDE.md — Legartis Contract Clause Tracker

## Mission
Build a small web app that lets a legal team upload contracts (plain text or markdown), label individual sentences with a clause type (e.g. "Limitation of Liability"), and view a dashboard with search/filter/grouping. Stack: FastAPI · Angular · PostgreSQL · Docker. Total budget: **3–4 hours**. The case study says explicitly *"backend code should be minimal"* — restraint is part of the grade.

## Four hard rules (Karpathy)
1. **Think before coding.** State assumptions out loud. Ask one clarifying question rather than guessing. Surface tradeoffs.
2. **Simplicity first.** Minimum code that solves the problem. No speculative features, no abstractions for a second caller that doesn't exist.
3. **Surgical changes.** Touch only what you must. Don't refactor adjacent code or remove pre-existing dead code unless asked.
4. **Goal-driven execution.** Every task ends with a verification step that proves the goal. Loop until verified.

## TDD contract
Every feature and every bug fix goes through the `red-green` skill (Pocock TDD). It auto-fires when the user says "implement X", "add the endpoint", "build the dashboard", "fix this bug", or similar — you don't need to type a slash. Or invoke explicitly with `/red-green`. One failing test → minimum code to pass → refactor only when green. Tests verify **behavior through the public interface** — no asserting on mock call counts, no reading private attributes. Tests must survive a behavior-preserving refactor.

## Stack conventions
**Backend** — FastAPI · Pydantic v2 · SQLAlchemy 2.0 async · asyncpg · Alembic · pytest + httpx + pytest-asyncio · Ruff (lint + format) · mypy strict.
**Frontend** — Angular v21+ · standalone components · Signals + `inject()` · new control flow (`@if`, `@for`, `@switch`) · Vitest · run `ng build` after every code change.
**Database** — PostgreSQL 16 in docker-compose. Schema changes only via Alembic migration. asyncpg driver. Never raw SQL strings — use SQLAlchemy 2.0 typed queries.
**Container** — single `docker-compose.yml` at repo root. `docker compose up` is the runnable deliverable per the case study.

## Verification loop (Boris Cherny's #1 quality multiplier)
Before declaring any task complete, run:
```bash
ruff check backend && ruff format --check backend && mypy backend
cd backend && pytest -x
cd ../frontend && npx tsc --noEmit && npx ng test --watch=false && npx ng build
docker compose up -d && curl -sf http://localhost:8000/healthz
```
Or just dispatch the `build-validator` subagent. **Never declare done until it returns "ready".**

## Review gate
Before any commit that finishes a feature, run the `full-review` skill. It auto-fires when the user says "ready to ship", "review this", "is this ready", "ready to merge" — no slash needed. Or invoke explicitly with `/full-review`. It dispatches in parallel: SOLID, DRY, test-quality, silent-failure-hunter, built-in `/code-review` (5-Sonnet pipeline), and `/security-review`. Blocking findings must be fixed before commit.

## Domain anti-patterns
- A clause is **a single sentence** by case-study definition. Don't merge or split sentences. Preserve original text byte-for-byte.
- Clause types are stored in a `clause_types` table with full CRUD (see [docs/adr/0001-dynamic-clause-types.md](docs/adr/0001-dynamic-clause-types.md)). The seed list is small (~7 common types). Don't pre-populate an exhaustive taxonomy — let users (and later the AI) add what they need.
- Uploaded files are plain text or markdown only. Don't add PDF/DOCX parsing — out of scope.
- Search/filter/grouping in the dashboard is server-side via query params (`?q=`, `?type=`, `?group_by=`). Don't ship client-side fuzzy search libraries.

## Repository layout
```
/                      docker-compose.yml, README.md, .gitignore
/backend               FastAPI app (pyproject.toml, app/, tests/, alembic/)
/frontend              Angular workspace (package.json, src/, etc.)
/docs                  case-study.pdf and any working notes (not in deliverable README)
/.claude               agents/, commands/, skills/, settings.json
```

## How to trigger workflows
Most workflows auto-fire from natural-language intent (no slash command needed):
- *"implement X" / "add the endpoint" / "build the dashboard"* → `red-green` (Pocock TDD)
- *"ready to ship" / "review this" / "is this ready"* → `full-review` (parallel reviewers)
- *"why is X failing" / "debug this"* → `diagnose` (loop-first debugging)
- *"plan how to X"* → `grill-with-docs` (domain-language scoping)

A `UserPromptSubmit` hook (`.claude/hooks/phrase-router.sh`) also injects deterministic reminders when these phrases are detected, so even if a skill auto-match misses you still get the workflow pointer.

Slash equivalents (always work): `/red-green`, `/full-review`, `/code-review`, `/security-review`, `/check`, `/verify`, `/run`.

## Skills loaded for this project
TDD methodology (`tdd`), debugging (`diagnose`), architecture critique (`improve-codebase-architecture`), domain-language planning (`grill-with-docs`), PRD synthesis (`to-prd`), pre-commit setup (`setup-pre-commit`), git safety (`git-guardrails-claude-code`), Angular v21+ official (`angular-developer`, `angular-new-app`), UI quality (`web-design-guidelines`).

## Documentation rules
- README at repo root explains setup and design decisions (this is a case-study deliverable).
- Anything else generated by Claude (review reports, analysis, debug notes) goes in `/docs` or stays in conversation — **not** at the repo root.
- Never commit secrets. `.env` is gitignored; provide `.env.example`.

## Lessons (grows as we work)
*Add a one-line rule each time Claude is corrected. Every line here exists because it solved a real problem.*

- _(empty — populate during build)_
