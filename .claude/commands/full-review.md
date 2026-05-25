---
description: Run all reviewers in parallel against the current diff (SOLID, DRY, test-quality, silent failures, built-in correctness, security). Use before declaring a feature done or before merge.
allowed-tools: Bash(git:*), Bash(gh:*), Task, Read, Grep, Glob
---

Orchestrate a full pre-merge review of the current diff.

# Step 1 — Resolve the diff range

```bash
BASE_SHA=${1:-$(git merge-base HEAD origin/main 2>/dev/null || git rev-parse HEAD~1)}
HEAD_SHA=$(git rev-parse HEAD)
git --no-pager log --oneline $BASE_SHA..$HEAD_SHA
git --no-pager diff --stat $BASE_SHA $HEAD_SHA
```

If the working tree is dirty, abort and tell the user to commit or stash first — reviewers compare commits, not uncommitted files.

# Step 2 — Dispatch all reviewers in parallel

In a single message, launch every reviewer below as a `Task` with `subagent_type: general-purpose` (or the specific agent name if registered). Pass each one the `BASE_SHA`, `HEAD_SHA`, and a one-line description of the change.

1. **solid-reviewer** — SOLID violations in the diff.
2. **dry-reviewer** — meaningful duplication (rule of three, same reason to change).
3. **test-quality-reviewer** — Pocock-style: tests verify behavior through public interfaces.
4. **silent-failure-hunter** (from pr-review-toolkit) — swallowed exceptions, ignored Promises, unhandled rejections.
5. **Built-in `/code-review`** (5-Sonnet parallel reviewer) — correctness bugs + CLAUDE.md compliance + git history context.
6. **Built-in `/security-review`** — OWASP-style security scan on the diff.

# Step 3 — Synthesize

Collect every finding. Group by severity:

```
## Full review — $BASE_SHA..$HEAD_SHA

### 🔴 Blocking
- [SOLID] backend/app/api/contracts.py:42 — SRP …
- [Security] backend/app/api/upload.py:18 — path traversal risk in filename …

### 🟡 Important
- [DRY] backend/app/api/contracts.py:50 and clauses.py:33 — duplicated normalisation
- [Tests] backend/tests/test_upload.py:14 — couples to mock call_count

### 🟢 Suggestions
- [Architecture] consider extracting ClauseRepository protocol …

### ✅ Strengths
- Tests cover the dashboard filter behavior end-to-end via httpx.
- Pydantic v2 models use `Annotated` constraints throughout.

**Verdict: <ready-to-merge | fix-blocking-then-ready | request-changes>**
```

# Step 4 — Act

- For **blocking** findings: do not declare the work done. Fix them, then re-run `/full-review`.
- For **important** findings: fix unless there's a defensible reason to defer (note it in CLAUDE.md's *Lessons* section).
- For **suggestions** and **strengths**: include them in the PR description but do not block on them.

# Rules

- Never re-run a reviewer just to "see if it changes its mind." If you disagree, push back in writing with reasoning.
- Always synthesize. A list of 6 raw outputs is not a review.
- If the diff is empty, abort and say so.
