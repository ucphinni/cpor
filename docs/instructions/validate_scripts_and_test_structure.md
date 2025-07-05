# Instructions: Validation Scripts and Test Structure

## Validation Scripts Location
- All validation scripts (e.g., `validate_task1.py`, `validate_spec_aligned.py`) must be placed under the `tests/` directory, not in the project root.
- Use a subdirectory such as `tests/validate/` for organization if there are multiple validation scripts.
- This keeps all test and validation logic together and makes the project structure clearer.

## Test Directory Structure
- Use the existing `tests/unit/` for unit tests.
- Use `tests/validate/` for protocol validation scripts and spec-alignment checks.
- Add `tests/integration/` if/when integration tests are needed.
- Do not create unnecessary new directories unless a new test type is introduced.

## General Test Hygiene
- All test fixtures must have explicit type annotations.
- All test and validation scripts must be PEP8 and mypy compliant.
- Remove unused variables and imports after refactoring.
- Run the full test suite and type checker after any major change.

---

**Summary:**
Keep all test and validation code under `tests/`, use subdirectories for organization, and maintain strict type and code hygiene throughout the project.
