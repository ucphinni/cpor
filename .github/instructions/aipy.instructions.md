# General Python Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, clean, maintainable Python code** suitable for **all layers of the project** (both sync and async). These instructions apply to **all modules**, regardless of context.

This is the **general baseline** that all specialized instruction sets (like async-core) inherit from.

---

## ✅ Priority: Correct, Minimal, and Testable Code

- Always produce **valid, working code** on the first try.  
- Favor **clarity** over cleverness.  
- Prioritize **testability** and **readability** over micro-optimization.  
- All code must be **easy to unit test with pytest**.  
- Use **complete type hints** everywhere.
- Enforce **deterministic behavior**: avoid hidden state, randomness without seeds, or context-sensitive results.  
- Write code that is **easy for both humans and AI to understand**.  

---

## ✅ Use Pure Functions Whenever Possible

- Favor **pure functions** that produce the same output for the same input and have **no side effects**.  
- Pure functions are easier to test, reuse, and refactor.  
- Isolate **impure** logic (I/O, DB calls, network requests) from pure data transformations.

**Example:**

~~~~python
def transform_input(data: dict) -> ProcessedData:
    ...
~~~~

---

## ✅ Use Early Returns and Guard Clauses

- Always handle **invalid** or **trivial** cases up front.  
- Bail out early to avoid nested conditionals.  
- Use guard clauses to make preconditions **explicit**.  
- Reduces **cognitive complexity** and **branching factor**.

**Example:**

~~~~python
def process_user(user: User) -> None:
    if not user.is_active:
        return
    # Do the real work
~~~~

---

## ✅ Avoid Code Duplication

- Always **refactor** repeated logic into reusable functions.  
- This reduces maintenance cost and errors.  
- Favor **clear, minimal helper functions** over inline repetition.

**Bad:**

~~~~python
def greet1(name: str) -> str:
    return f"Hello, {name}!"

def greet2(name: str) -> str:
    return f"Hello, {name}!"
~~~~

**Good:**

~~~~python
def greet(name: str) -> str:
    return f"Hello, {name}!"
~~~~

---

## ✅ Function Size and File Size Limits

- **Source files** should generally stay **under ~400 lines**.  
  - Split large modules into submodules as needed.  
- **Function definitions** should fit comfortably on screen.  
  - Aim for ~20–40 lines max per function unless there's a clear, justified reason.  
- Tests can be larger but should remain **logically organized**.

---

## ✅ Use Type Hints Everywhere

- **All** public function signatures must have complete type hints.  
- Type hints make code **self-documenting** and **statistically analyzable**.  
- Use **mypy** to enforce static type correctness.

**Example:**

~~~~python
def add(a: int, b: int) -> int:
    return a + b
~~~~

---

## ✅ Docstring Standards

- Use **Google-style** or **standard Python** docstrings.  
- Describe **purpose**, **arguments**, **return values**, and **exceptions** if any.  

**Example:**

~~~~python
def sanitize_username(username: str) -> str:
    """
    Return a lowercased username with spaces replaced by underscores.

    Args:
        username (str): The username to sanitize.

    Returns:
        str: The sanitized username.
    """
    return username.strip().lower().replace(" ", "_")
~~~~

---

## ✅ Testing Standards

- All production code must have **accompanying unit tests**.  
- Use **pytest** for all testing.  
- Tests must be **clear**, **minimal**, and **cover expected behavior**.  
- Use **mocks** or **fakes** to isolate dependencies.  
- For **async code**, use **pytest-asyncio**.

**Example test (sync):**

~~~~python
def test_add() -> None:
    assert add(2, 3) == 5
~~~~

**Example test (async):**

~~~~python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_data() -> None:
    mock_fetch = AsyncMock(return_value={"key": "value"})
    data = await mock_fetch("http://example.com")
    assert data == {"key": "value"}
~~~~

---

## ✅ Static Analysis and Linting

- All code must pass **MyPy** for static type checking.  
- All code must pass **Ruff** for linting.  
- This ensures **style consistency**, **correctness**, and **AI-friendly structure**.

---

## ✅ General Anti-Patterns to Avoid

- Excessive nesting / deeply nested logic.  
- Broad `except:` that hides errors without logging context.  
- Hidden or mutable global state.  
- Duplicate code or logic.  
- Unclear naming or cryptic variable names.  
- Huge unbroken functions or classes that can't be unit tested.

---

## ✅ Example of Clean, Testable Design

**Production code:**

~~~~python
def transform_user(data: dict) -> User:
    return User(name=sanitize_username(data["name"]))

async def save_user(data: dict, db) -> None:
    user = transform_user(data)
    await db.save(user)
~~~~

**Test code:**

~~~~python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_save_user() -> None:
    mock_db = AsyncMock()
    await save_user({"name": "John Doe"}, mock_db)
    mock_db.save.assert_awaited_once()
~~~~

---

## ✅ Summary

- Produce **correct, testable, maintainable** Python code.  
- Use **pure functions** wherever possible.  
- Guard clauses and early returns to reduce complexity.  
- Type hints everywhere, enforced by **MyPy**.  
- Lint with **Ruff**.  
- Unit tests with **pytest** (and **pytest-asyncio** for async code).  
- Enforce **file and function size** limits.  
- Avoid code duplication.  
- Use **clear docstrings** for all public functions.  

---

*This "General Python Instructions" file is designed to be inherited by all other specialized instruction sets, ensuring consistency and quality across the entire project.*