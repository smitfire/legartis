# API Reference

The backend exposes **8 HTTP endpoints**. Interactive Swagger UI is available at
<http://localhost:8000/docs> when the stack is running, and OpenAPI JSON at
<http://localhost:8000/openapi.json>.

All responses are JSON. Errors use the FastAPI default shape:

```json
{ "detail": "human-readable message" }
```

---

## `GET /healthz`

Container health probe. Always returns 200 once the app has started.

```bash
curl http://localhost:8000/healthz
# → {"ok": true}
```

---

## `GET /clause-types`

Returns the seven seed clause types as `[{value, label}]`. Static enum — does
not hit the database.

```bash
curl http://localhost:8000/clause-types
```

```json
[
  { "value": "limitation_of_liability",   "label": "Limitation of Liability" },
  { "value": "termination_for_convenience","label": "Termination for Convenience" },
  { "value": "non_compete",               "label": "Non-Compete" },
  { "value": "confidentiality",           "label": "Confidentiality" },
  { "value": "governing_law",             "label": "Governing Law" },
  { "value": "indemnification",           "label": "Indemnification" },
  { "value": "force_majeure",             "label": "Force Majeure" }
]
```

The `value` is the machine identifier persisted in `labels.clause_type`. The
`label` is the human-friendly display string.

---

## `GET /clause-type-counts?q=`

Returns the seven seed clause types **with the number of distinct documents
labelled with each type**. The dashboard uses this to render counts on its
filter chips and disable chips whose count is `0`.

| Query param | Type | Required | Behaviour |
|---|---|---|---|
| `q`         | string | no | Restrict counts to documents whose title or content matches `q` (case-insensitive). |

The endpoint **ignores** any selected types — chip selections are OR'd, so the
count for type `B` should reflect "how many more documents would I see if I
clicked B," which doesn't depend on whether type `A` is already selected.

```bash
curl 'http://localhost:8000/clause-type-counts?q=liability'
```

```json
[
  { "value": "limitation_of_liability", "label": "Limitation of Liability", "count": 1 },
  { "value": "confidentiality",          "label": "Confidentiality",          "count": 0 },
  …
]
```

Types with zero matching documents always appear with `count: 0` — the
response is **always** the full seven entries so the frontend can render the
filter row deterministically.

---

## `POST /documents`

Upload a `.txt` or `.md` contract. The body is `multipart/form-data` with a
single `file` field.

```bash
curl -X POST http://localhost:8000/documents \
  -F 'file=@my-contract.md'
```

Pipeline:

1. Read the file as UTF-8. Non-UTF-8 → `415 Unsupported Media Type`.
2. Strip markdown leaders (`#`, `>`, `-`, `1.`) per line.
3. Segment with `pysbd` (legal-aware sentence boundaries).
4. Persist the document + its sentences in a single transaction.

Returns `201 Created` with the full document including segmented sentences:

```json
{
  "id": 42,
  "title": "my-contract.md",
  "uploaded_at": "2026-05-25T11:00:21.563317Z",
  "sentences": [
    { "id": 100, "position": 0, "text": "Master Services Agreement", "labels": [] },
    { "id": 101, "position": 1, "text": "This Agreement is entered into…", "labels": [] }
  ]
}
```

---

## `GET /documents`

The dashboard query. Search, filter, and group in a single endpoint.

| Query param | Type | Behaviour |
|---|---|---|
| `q`         | string | Case-insensitive match against title and content. |
| `type`      | string (repeatable) | Clause-type filter. Multi-select is **OR**'d. |
| `group_by`  | `"type"` | Switches the response envelope to `GroupedDocuments`. |

### Default (flat) response shape

```bash
curl http://localhost:8000/documents
```

```json
[
  {
    "id": 4,
    "title": "02-master-services-agreement.md",
    "uploaded_at": "2026-05-25T11:00:21.563317Z",
    "sentence_count": 16,
    "label_count": 2,
    "clause_types": ["governing_law", "limitation_of_liability"]
  }
]
```

### Grouped response shape

```bash
curl 'http://localhost:8000/documents?group_by=type'
```

```json
{
  "groups": [
    {
      "clause_type": "confidentiality",
      "documents": [{ "id": 1, "title": "nda.txt", ... }]
    }
  ]
}
```

Documents appear under **every** clause type they carry at least one label of —
this is a multi-bucket result, not a clean partition.

### Multi-filter example

```bash
curl 'http://localhost:8000/documents?q=services&type=confidentiality&type=non_compete'
```

Returns documents whose title or content matches `services` **AND** which carry
at least one Confidentiality **OR** Non-Compete label.

---

## `GET /documents/{document_id}`

Full document including sentences with their labels. Used by the per-document
detail page.

```bash
curl http://localhost:8000/documents/42
```

```json
{
  "id": 42,
  "title": "my-contract.md",
  "uploaded_at": "2026-05-25T11:00:21.563317Z",
  "sentences": [
    {
      "id": 100,
      "position": 0,
      "text": "Master Services Agreement",
      "labels": []
    },
    {
      "id": 104,
      "position": 4,
      "text": "In no event shall either party's total cumulative liability…",
      "labels": [
        {
          "id": 12,
          "sentence_id": 104,
          "clause_type": "limitation_of_liability",
          "source": "MANUAL",
          "confidence": null,
          "created_at": "2026-05-25T11:00:53.123Z"
        }
      ]
    }
  ]
}
```

Unknown `document_id` → `404 Not Found`.

---

## `POST /sentences/{sentence_id}/labels`

Apply a clause-type label to a sentence.

```bash
curl -X POST http://localhost:8000/sentences/104/labels \
  -H 'Content-Type: application/json' \
  -d '{"clause_type": "limitation_of_liability"}'
```

Returns `201 Created` with the new label.

Error model:

| Status | Cause |
|---|---|
| `404` | Sentence does not exist. |
| `409` | A label with the same `(sentence_id, clause_type)` already exists. |
| `422` | `clause_type` is not one of the seven seed values, or another schema/CHECK violation. |

The distinction between 409 and 422 matters: the `IntegrityError` handler
inspects the database message — a `UNIQUE` violation becomes 409 *idempotently*,
all other constraint violations become 422 so a malformed payload isn't masked
as "duplicate".

---

## `DELETE /labels/{label_id}`

Remove a label. Returns `204 No Content` whether or not the label existed
(the operation is idempotent — the post-condition is the same).

```bash
curl -X DELETE http://localhost:8000/labels/12
```

---

## Cross-cutting concerns

- **CORS**. `app.config.settings.cors_origins` defaults to `["http://localhost:4200"]`. Adjust via env var.
- **Pagination**. None — fine at case-study scale. The README's "What's intentionally not here" section discusses when to add it.
- **Auth**. None. The schema is single-tenant. Multi-tenant + RBAC is a
  documented extension; the chokepoint is `app/deps.py:get_db` where a
  `current_org` dependency would slot in.
- **Rate limiting**. None at the app layer. Would live in nginx or an upstream
  gateway.
