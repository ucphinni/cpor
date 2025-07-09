# Coding Instructions for GitHub Copilot Chat

You are an AI assistant that writes **simple, clean, and minimal Python code** focused on **ease of testing and readability**.

---

## 🚀 Priority: Correct, Simple, and Testable Code

You are an AI assistant whose top priority is to produce **correct, testable, and maintainable code that works the first time**.

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
- **Correctness first** — always produce valid, working code on the first try.
- Favor **idiomatic async/await** patterns.
- Avoid blocking the event loop (no sync I/O in async functions or methods).
- Minimize branching and deeply nested logic.
- Code should be **easy to unit test with pytest**.

---

Example of pure + testable design:

```python
def transform_input(data: dict) -> "ProcessedData":
    # Pure function — easy to test
    ...

async def handle_request(data: dict, db) -> None:
    # Impure part isolated
    processed = transform_input(data)
    await db.save(processed)
```

---

## ✅ Use Pure Functions Whenever Possible

- Favor **pure functions** that always produce the same output for the same input and have **no side effects**.  
- Pure functions are easier to test, easier to reuse, and safer to refactor.  
- They make reasoning about the code simpler for both humans and AI.  
- Pure functions are **AI-friendly** because they don’t depend on external context or hidden state, making them easier to generate correctly on the first try.  
- Separate your code into **pure logic** (thinking) and **impure actions** (doing), isolating I/O, database calls, and network requests outside pure functions.

Example of a pure function:

```python
def sanitize_username(username: str) -> str:
    """
    Return a lowercased username with spaces replaced by underscores.
    """
    return username.strip().lower().replace(" ", "_")
```

Example of separating pure and impure:

```python
def transform_user(data: dict) -> "User":
    return User(name=sanitize_username(data["name"]))

async def save_user(data: dict, db) -> None:
    user = transform_user(data)
    await db.save(user)
```

---

## ✅ Use Bailout Returns and Guard Clauses to Reduce Complexity

- Handle simple, invalid, or edge cases **up front** using early returns or guard clauses.  
- This approach minimizes nesting and branching in the main logic, leading to clearer and more maintainable code.  
- Think of this like reducing algorithmic complexity from potentially quadratic (N²) to linear (N) in terms of cognitive load and code paths:
  - By quickly **bailing out** of simple cases, you avoid deeply nested conditionals that multiply complexity.
  - The remaining core logic is simpler, more focused, and easier to test.  
- Guard clauses are explicit precondition checks that exit early:
  - They protect your main logic from invalid states.  
  - They make the code’s intent immediately obvious to readers and maintainers.  
- Use bailout returns and guard clauses to **whittle away easy cases first**, leaving only the complex logic to handle after all simple conditions are eliminated.

Example:

```python
async def handle_message(msg: dict) -> None:
    if not is_valid(msg):
        return  # Bail out early on invalid message

    if is_heartbeat(msg):
        await respond_heartbeat(msg)
        return  # Bail out after handling simple heartbeat

    # Complex business logic happens here with validated message
    await process_business_logic(msg)
```

---

## ✅ Unit Tests Must Be Written Alongside the Code

- Always provide **minimal, clear unit tests** at the same time as the production code.  
- Tests must cover the *main behavior* of the code immediately.  
- Use **simple mocks or fakes** as needed.  
- Ensure tests demonstrate **correct, expected behavior**.  
- Tests should use standard Python test frameworks (e.g., `pytest`).  
- Prefer **idiomatic Python style** in both production and test code.

Example:

```python
# Production code
def add(a: int, b: int) -> int:
    return a + b

# Test
def test_add() -> None:
    assert add(2, 3) == 5
```

---

## ✅ Explicitly Use Pytest for Testing

- Use **pytest** for all unit tests.  
- Write tests as **simple functions** (no need for classes unless necessary).  
- Use **pytest fixtures** and **mocks** if needed.  
- Mark async tests with `@pytest.mark.asyncio` when required.  
- CI systems should **run pytest automatically** to verify correctness.

Example async test with pytest:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_data() -> None:
    mock_fetch = AsyncMock(return_value={"key": "value"})
    data = await mock_fetch("http://example.com")
    assert data == {"key": "value"}
```

---

## ✅ File Size Limits

- **Source code files:** Enforce a strict maximum of **~400 lines** per source code file.  
  - Automatically split code into logical modules when approaching this limit.  
  - Keep source files focused, concise, and maintainable.
- **Test files:** Be more relaxed on size limits.  
  - Tests for related modules or features can be grouped together even if exceeding 400 lines.  
  - Aim for readability and logical grouping rather than strict line count.

---

## ✅ Example Function Docstring Style

```python
async def fetch_data(url: str) -> dict:
    """
    Fetch data asynchronously from a URL.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        dict: Parsed JSON response.
    """
    ...
```

---

## ✅ Example: Pure Function for CMOS to HTML Conversion

```python
from typing import Dict

def cmos_to_html(cmos_data: Dict[str, int]) -> str:
    """
    Convert CMOS date/time values to a formatted HTML string.

    Args:
        cmos_data (Dict[str, int]): Dictionary containing CMOS time fields such as
            'year', 'month', 'day', 'hour', 'minute', 'second'.

    Returns:
        str: HTML-formatted date/time string.
    """
    year = cmos_data.get('year', 0)
    month = cmos_data.get('month', 0)
    day = cmos_data.get('day', 0)
    hour = cmos_data.get('hour', 0)
    minute = cmos_data.get('minute', 0)
    second = cmos_data.get('second', 0)

    # Format date/time into a string
    date_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    # Return as HTML string (e.g., wrapped in a <time> tag)
    return f"<time datetime='{date_str}'>{date_str}</time>"
```

---

## ✅ Avoid Repeating Code and Favor Function Reuse

- **Avoid repeating code**. If you see similar logic or patterns, **refactor it into reusable functions**.  
- Function reuse improves clarity, reduces errors, and makes the codebase easier to maintain and test.  
- Always **watch for opportunities to consolidate** duplicate or similar code blocks into well-named helper functions.  
- Aim for **concise code** that is readable without unnecessary verbosity or redundant comments.  
- Avoid unnecessary punctuation or overly verbose constructs that clutter the code.  
- Providing clear, minimal examples helps the AI understand and adopt this style naturally.

### Example: Repetitive code vs reusable function

**Repetitive (to avoid):**

```python
def greet_user1(name: str) -> str:
    return f"Hello, {name}!"

def greet_user2(name: str) -> str:
    return f"Hello, {name}!"

def greet_user3(name: str) -> str:
    return f"Hello, {name}!"
```

**Refactored with reuse (preferred):**

```python
def greet_user(name: str) -> str:
    return f"Hello, {name}!"
```

### Example: Concise code instead of verbose

**Verbose (to avoid):**

```python
if is_valid:
    return True
else:
    return False
```

**Concise (preferred):**

```python
return is_valid
```

---

## ✅ Summary

- Prioritize **correct, testable, and maintainable code that works first time**.  
- Use **pure functions** wherever possible.  
- Use **bailout returns and guard clauses** to minimize complexity.  
- Write **unit tests alongside code**, using **pytest** as the standard framework.  
- Enforce a strict **~400-line limit on source code files** for modularity.  
- Be more relaxed on test file size but keep tests organized.  
- Use consistent **type hints and Google-style docstrings** for clarity and static analysis.  
- Prefer **idiomatic Python** style and expressions.
