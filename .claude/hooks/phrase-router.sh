#!/usr/bin/env bash
# UserPromptSubmit hook — detects intent phrases and injects workflow reminders.
# stdout is appended to Claude's context before the prompt is processed.
# Stay silent unless a real trigger matches; otherwise we add noise to every turn.

set -euo pipefail

# Claude Code passes the user's prompt via stdin as JSON: { "prompt": "...", ... }
input=$(cat)
prompt=$(printf '%s' "$input" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("prompt",""))' 2>/dev/null || echo "")

# Lowercase for matching
lc=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

emit() { printf '\n[workflow router] %s\n' "$1"; }

# --- Pre-merge / review intent --------------------------------------------
if printf '%s' "$lc" | grep -Eq '\b(ship( it)?|ready to (ship|merge|commit)|merge( this)?|is this ready|done|finished|review( this| the)?( diff)?|audit (this|the) (change|diff)|pre-?merge)\b'; then
  emit "Detected pre-merge intent. Invoke the full-review skill (parallel SOLID + DRY + test-quality + silent-failure + /code-review + /security-review) before declaring done. Then dispatch the build-validator subagent."
fi

# --- New feature / TDD intent ---------------------------------------------
if printf '%s' "$lc" | grep -Eq '\b(implement|add (a |the |new )?(feature|endpoint|route|component|page|button|service)|build (the |a |an )?|let'\''s (build|add|create)|write (the |a )?(function|method|endpoint|component)|start a new feature|new feature|fix this bug|fix the bug)\b'; then
  emit "Detected new-behavior intent. Invoke the red-green skill (Pocock TDD: one failing test → minimum impl → refactor). Do not write production code without a failing test first."
fi

# --- Debugging intent -----------------------------------------------------
if printf '%s' "$lc" | grep -Eq '\b(debug|why is|why does|broken|failing|crashes?|not working|throws|error|stack trace)\b'; then
  emit "Detected debugging intent. Invoke the diagnose skill: build a fast reproducible feedback loop first, then hypothesize. No staring at code without a loop."
fi

# --- Planning / scoping intent --------------------------------------------
if printf '%s' "$lc" | grep -Eq '\b(plan|how should|what should we|scope|approach|design|architecture)\b'; then
  emit "Detected planning intent. Prefer plan mode (Shift+Tab x2) or the grill-with-docs skill for interview-style requirements gathering before coding."
fi

exit 0
