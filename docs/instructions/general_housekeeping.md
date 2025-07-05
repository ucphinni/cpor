# Instructions: General Housekeeping for CPOR Project

## Always
- Keep all test, validation, and utility scripts under the `tests/` directory.
- Use explicit type annotations for all fixtures and test function parameters.
- Remove unused variables and imports after any refactor.
- Keep docstrings and comments up to date with code changes.
- Run the full test suite and type checker after every major change.
- Ensure all message schemas and tests are strictly spec-aligned.

## When Adding New Test Types
- Use `tests/unit/` for unit tests.
- Use `tests/validate/` for protocol validation and spec-alignment scripts.
- Use `tests/integration/` for integration tests if/when needed.

## When Refactoring
- Move any validation scripts from the project root to `tests/validate/`.
- Update documentation to reflect any changes in structure or conventions.

---

**Summary:**
Maintain a clean, organized, and type-safe codebase. Keep all test and validation logic under `tests/`, and document all conventions and lessons learned in the `docs/` directory.
