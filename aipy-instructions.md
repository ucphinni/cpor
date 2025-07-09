# Coding Instructions for GitHub Copilot Chat

You are an AI assistant that writes **simple, clean, and minimal Python code** focused on **ease of testing and readability**.

---

## 🚀 Priority: Correct, Simple, and Testable Code

- Prioritize **clarity** and **simplicity** over cleverness.  
- Minimize branching and deeply nested logic.  
- Favor **pure functions** that are easy to test in isolation and for data transformation.  
- Use **early returns / guard clauses** to reduce complexity.  
- Always **add complete type hints** to make code self-documenting and statically checkable.  
- Write code that is **easy to unit test with pytest** with minimal mocks or fakes.  
- Emphasize **deterministic, predictable behavior**.  
- Split impure, side-effecting code from pure logic for better testability and maintainability.  
- **Write unit tests in parallel** with production code — aim for 100% coverage.  
- When in doubt, **choose the design that is easiest to test**.  
- **Correctness first** — code should work on the first try.  
- Favor **idiomatic async/await** patterns.  
- Avoid blocking the event loop (no sync I/O in async functions).  

---

## ✅ Use Pure Functions Whenever Possible

- Pure functions always produce the same output for the same input and have **no side effects**.  
- Easier to test, reuse, and safe to refactor.  
- Separate **pure logic** (thinking) from **impure actions** (doing).  

~~~~python
def sanitize_username(username: str) -> str:
    """Return a lowercased username with spaces replaced by underscores."""
    return username.strip().lower().replace(" ", "_")
~~~~

~~~~python
def transform_user(data: dict) -> "User":
    return User(name=sanitize_username(data["name"]))

async def save_user(data: dict, db) -> None:
    user = transform_user(data)
    await db.save(user)
~~~~

---

## ✅ Use Bailout Returns and Guard Clauses to Reduce Complexity

- Handle invalid or edge cases **up front** with early returns.
- Keeps main logic flat and straightforward.

~~~~python
async def handle_message(msg: dict) -> None:
    if not is_valid(msg):
        return  # early exit

    if is_heartbeat(msg):
        await respond_heartbeat(msg)
        return  # simple case handled

    await process_business_logic(msg)
~~~~

---

## ✅ Unit Tests Must Be Written Alongside the Code

- Provide **minimal, clear unit tests** alongside production code.
- Cover main behavior immediately, using **pytest**.
- Use **simple mocks or fakes** as needed.

~~~~python
def add(a: int, b: int) -> int:
    return a + b

def test_add() -> None:
    assert add(2, 3) == 5
~~~~

---

## ✅ Explicitly Use Pytest for Testing

- Use **pytest** for all unit tests.
- Simple test functions; async tests use `@pytest.mark.asyncio`.
- Ensure CI runs pytest automatically.

~~~~python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_data() -> None:
    mock_fetch = AsyncMock(return_value={"key": "value"})
    data = await mock_fetch("http://example.com")
    assert data == {"key": "value"}
~~~~

> Note: `pytest-asyncio` v1.0+ has removed the `event_loop` fixture in favor of `@pytest.mark.asyncio(loop_scope="...")` and `asyncio.get_running_loop()` ([thinhdanggroup.github.io](https://thinhdanggroup.github.io/pytest-asyncio-v1-migrate/?utm_source=chatgpt.com)).

---

## ✅ File Size Limits

- **Source code files:** max ~400 lines; split into modules as needed.
- **Test files:** more lenient; group related tests for readability.

---

## ✅ Example Function Docstring Style

~~~~python
async def fetch_data(url: str) -> dict:
    """
    Fetch data asynchronously from a URL.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        dict: Parsed JSON response.
    """
    ...
~~~~

---

## ✅ Example: Pure Function for CMOS to HTML Conversion

~~~~python
from typing import Dict

def cmos_to_html(cmos_data: Dict[str, int]) -> str:
    """
    Convert CMOS date/time values to a formatted HTML <time> tag.

    Args:
        cmos_data: Fields like 'year', 'month', 'day', 'hour', 'minute', 'second'.

    Returns:
        HTML string representing the date/time.
    """
    year = cmos_data.get('year', 0)
    month = cmos_data.get('month', 0)
    day = cmos_data.get('day', 0)
    hour = cmos_data.get('hour', 0)
    minute = cmos_data.get('minute', 0)
    second = cmos_data.get('second', 0)

    date_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return f"<time datetime='{date_str}'>{date_str}</time>"
~~~~

---

## ✅ Avoid Repeating Code and Favor Function Reuse

- Avoid duplicated logic—refactor into named helper functions.
- Prefer concise expressions over verbose constructs.

---

## ✅ Formatting & Linting Recommendations

- Use **Black** or **Ruff format** as auto-formatters.
- Ruff is a **fast, all-in-one linter + formatter** that plays nicely with Black configs ([docs.astral.sh](https://docs.astral.sh/ruff/formatter/?utm_source=chatgpt.com), [github.com](https://github.com/astral-sh/ruff?utm_source=chatgpt.com)).
- Add `ruff`, `black`, or both to CI and/or pre-commit hooks:

~~~~toml
[tool.ruff]
line-length = 88

[tool.ruff.format]
quote-style = "single"
docstring-code-format = true
~~~~

---

## ✅ Summary

- **Correctness first** — code should work on first run.
- **Pure functions**, **guard clauses**, **type hints**, **Google-style docstrings**.
- Tests alongside production code, with **pytest** and async support.
- File limits for modularity; tests can be grouped.
- **DRY**, concise code, idiomatic Python.
- Auto-format and lint with **Black** / **Ruff**.
