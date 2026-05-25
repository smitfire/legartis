---
description: Enter Pocock's TDD red-green-refactor loop for one vertical slice. Use before writing any production code for a new feature or bug fix.
allowed-tools: Read, Edit, Write, Bash(pytest:*), Bash(npx ng test:*), Bash(npm test:*), Glob, Grep
---

Invoke the `tdd` skill and execute the red-green-refactor loop on exactly **one** vertical slice.

# Hard rules (from Pocock's `tdd` skill)

1. **One failing test at a time.** Do not write a second test until the current one is green.
2. **Test verifies behavior through the public interface.** No mocking of internal collaborators. No reading private attributes.
3. **Minimum implementation to make this one test pass.** No speculative features. No extra branches "for completeness."
4. **Refactor only when green.** Improve names, structure, duplication — but tests must stay green throughout.
5. **Tracer-bullet first.** The first slice is the simplest path through the system end-to-end, even if it returns a hard-coded value.

# Workflow

1. **State the behavior** you're about to test in one sentence. Have me confirm before writing code.

2. **Write ONE failing test** that describes the behavior from the outside. Name it after the behavior, not the function. Run it and confirm it fails for the right reason (not an import error).

   ```bash
   # Backend
   cd backend && pytest <new_test_path> -x --tb=short
   # Frontend
   cd frontend && npx ng test --watch=false --include='<new_spec_path>'
   ```

3. **Write the minimum code** to make that test pass. Run the test. Confirm green.

4. **Refactor** if there's an obvious improvement that keeps tests green. Otherwise skip.

5. **Decide the next slice.** State the next behavior. Wait for confirmation. Loop.

# Anti-patterns to refuse

- Writing the full test suite up front "to plan" — those tests validate imagined behavior, not real behavior.
- Implementing more than the current test demands — every extra branch is untested production code.
- Mocking the database, HTTP client, or any internal class — use a real test instance (in-memory SQLite for unit tests, real Postgres in a `docker compose up -d db` for integration).
- Asserting on a mock's call count — assert on the user-visible result instead.

# When NOT to TDD

- Pure prototyping where you don't yet know the shape (use Pocock's `prototype` skill — *not* installed here; just say so and proceed without tests, marked "spike — discard before merge").
- Trivial config files, README edits, glue code with no logic.

In every other case for this project, TDD is the contract. Tests are not "bonus" — they are how we know the code works.
