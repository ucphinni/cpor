# AsyncCore Instructions for GitHub Copilot Chat

You are an AI assistant that writes **simple, clean, and minimal Python async core logic** designed for **correctness, testability, and production readiness**. These instructions assume they are used alongside the general and async app layers.

---

## ✅ Priority: Correct, Minimal, Testable Async Core

- Read [Link to aipy.instructions.md](aipy.instructions.md)
- Write **unit tests** with **pytest-asyncio** alongside code.
- Also, code should be **easy to unit test with pytest and pytest-asyncio**.

---

## ✅ Use TaskGroup.create_task() for Background Work

- Prefer **asyncio.TaskGroup** (Python 3.11+) to launch and track background tasks.
- TaskGroup must be constructed at the **top-level async main** function or passed into objects while still in scope.
- Ensures **all tasks complete or cancel** cleanly on shutdown.
- Avoid "fire and forget" coroutines; all tasks must be **awaited or tracked**.

**Example:**

~~~~python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker1())
        tg.create_task(worker2())
~~~~

---

## ✅ Graceful Cancellation with CancelledError

- Always **catch** `asyncio.CancelledError` in loops or cleanup code.
- Do **clean shutdown work** before exiting.
- **Re-raise** after handling so cancellation is propagated correctly.

**Example:**

~~~~python
async def worker():
    try:
        while True:
            await do_work()
    except asyncio.CancelledError:
        await cleanup()
        raise
~~~~

---

## ✅ Await All Subtasks and Shield Critical Sections

- Use **await** everywhere coroutines are called.
- Never return unawaited coroutines by mistake.
- Use **asyncio.shield()** for critical sections that *must* finish even if cancellation happens.

**Example:**

~~~~python
await asyncio.shield(save_important_data())
~~~~

---

## ✅ Explicit Timeouts on I/O

- Always specify **reasonable timeouts** on network or DB calls.
- Prevents hanging tasks and wasted resources.
- Default to **short, sensible values**.

**Example:**

~~~~python
response = await client.get(url, timeout=5)
~~~~

---

## ✅ Exception Handling in Async Functions

- Use **try/except** around expected error conditions.
- Log with **contextual info** to aid debugging.
- Avoid broad excepts that swallow tracebacks or hide failures.

**Example:**

~~~~python
async def fetch_data(url: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        raise
~~~~

---

## ✅ Avoid Mixing Sync and Async Calls

- **Never** call blocking sync I/O in `async def`.
- Always use async libraries (`aiofiles`, `aiosqlite`, `aiopg`, `httpx`).
- This avoids blocking the event loop and ensures true concurrency.

**Bad:**

~~~~python
async def load():
    data = requests.get("https://example.com")  # ❌ Blocking
    return data.text
~~~~

**Good:**

~~~~python
import httpx

async def load():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
        return response.text
~~~~

---

## ✅ Enforce Async File I/O

- All **file reading/writing** in `async def` must use **aiofiles** (or another non-blocking async library).
- Blocking built-in `open()` and file methods are **prohibited** in async functions.
- Use async context managers with **aiofiles.open()**.
- Handle **chunked and random access** using aiofiles APIs.
- See **aiofiles-async.md** for detailed patterns and guardrails.

---

## ✅ Static Analysis with MyPy and Ruff

- Code **must pass** static type checks with **MyPy**.
- Code **must be linted** with **Ruff**.
- Enforce **consistent, complete type hints**.
- Clean code = easier for AI to extend correctly.

---

## ✅ Unit Test Expectations

- Write **unit tests in parallel** with production code.
- Target **100% test coverage** of async logic.
- Tests must be **minimal, clear, deterministic**.
- Use **pytest-asyncio** for async test support.
- Use **AsyncMock** to isolate async dependencies.

**Example test structure:**

~~~~python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_process_data():
    mock_client = AsyncMock(return_value={"result": "ok"})
    result = await process_data(mock_client)
    assert result["result"] == "ok"
~~~~

---

## ❌ Anti-Patterns

- Spawning tasks without using an `asyncio.TaskGroup` or otherwise tracking them.
- Catching overly broad exceptions (e.g. bare `except:`) without logging context.
- Mixing sync I/O or blocking calls in `async def`.
- Returning or ignoring unawaited coroutines.

## 🛠 Logging and Observability

- Use structured logging (e.g., JSON) with contextual fields: `module`, `function`, `request_id`, `timestamp`, and `level`.
- Include clear, consistent log messages for task start/stop, errors, and key events.
- Use the standard `logging` module or a structured logger like `structlog`.

---

## ✅ Summary

- **Correct, testable, idiomatic async core**.
- Use **TaskGroup** for safe concurrency.
- Handle **CancelledError** with care, always **re-raise**.
- Await **all** subtasks; never leave work untracked.
- Use **asyncio.shield** for critical sections.
- Set **explicit timeouts** for all I/O.
- Never mix sync calls in async contexts.
- **Enforce async file I/O** with aiofiles.
- Write unit tests with **pytest-asyncio** and **AsyncMock**.
- Pass static analysis with **MyPy** and **Ruff**.
- Maintain **full type hints** and **100% test coverage**.