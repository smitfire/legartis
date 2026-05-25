# Legartis Contract Clause Tracker

A small web app for legal teams to upload contracts, label individual sentences with a clause type, and explore the dataset through a searchable, filterable dashboard.

> Built against the Legartis full-stack case study. Scope: minimal backend, intuitive UX, ~3–4 hours of work.

## Stack

- **Backend** — FastAPI · SQLAlchemy 2.0 async · Alembic · `pysbd` for sentence segmentation
- **Frontend** — Angular 21 (standalone components, signals, new control flow) · Angular Material (M3)
- **Database** — PostgreSQL 16 (Docker)
- **Tests** — pytest + httpx (backend), Vitest (frontend), Playwright (e2e)
- **Container** — single `docker-compose.yml` at repo root

## Quick start

```bash
docker compose up --build
# → frontend: http://localhost:4200
# → API docs: http://localhost:8000/docs
```

## Domain in one diagram

```
Document  1 ── n  Sentence  1 ── n  Label  ── clause_type (enum: 7 values)
                                              source       (MANUAL | AUTO)
                                              confidence   (nullable)
```

A clause is always **a single sentence** (case-study definition).

## More

- See `docs/case-study.pdf` for the original brief.
- Design decisions: see [Design decisions](#design-decisions) below (filled in as the build progresses).

## Design decisions

_(filled in throughout the build — currently scaffolding.)_
