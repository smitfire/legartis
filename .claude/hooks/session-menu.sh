#!/usr/bin/env bash
# SessionStart hook — prints a compact workflow menu and project state.
# stdout is injected as context for Claude at session start.

set -euo pipefail

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(no git)")
last=$(git log -1 --oneline 2>/dev/null || echo "(no commits)")
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

cat <<EOF

=== Legartis project workflows (auto-trigger by intent — no slash needed) ===

* TDD a new behavior        say: "implement X" / "add the X endpoint" / "build the dashboard"
  → fires red-green skill (Pocock red→green→refactor)

* Pre-merge review          say: "ready to ship" / "review this" / "is this ready"
  → fires full-review skill (parallel SOLID + DRY + tests + silent-failure + /code-review + /security-review)

* Debug a failure           say: "why is X failing" / "debug this" / "broken"
  → fires diagnose skill (loop-first debugging)

* Plan before coding        Shift+Tab x2 (plan mode), or say "plan how to X"
  → fires grill-with-docs skill for domain-language scoping

Slash equivalents still work: /full-review · /red-green · /code-review · /security-review · /verify · /run

Branch: $branch   Last commit: $last   Dirty files: $dirty
EOF

exit 0
