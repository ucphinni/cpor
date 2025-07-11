# Async Core Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, production-ready, minimal, testable Python async core logic**.  

> 🟢 **DEFAULT MODE: Everything is async.**  
> 🟠 Sync code is allowed ONLY as an explicitly managed edge case.  
> 🚫 Avoid all blocking calls in `async def` unless *properly wrapped*.  

---

## ✅ 📌 Priority Goals

- Correctness first — valid, working code the first time.
- Async everywhere by default.
- Fully testable with pytest and pytest-asyncio.
- Minimal, clear, idiomatic Python 3.11+ async/await style.
- Clear guardrails to avoid AI "guesswork" or incorrect patterns.
- Designed for production service use.

---

## ✅ General Rules

- All I/O and network calls must be **async**.
- No blocking calls in async functions.  
- Use **await** everywhere for coroutines.  
- Use **asyncio.TaskGroup** for concurrency.  
- Use **explicit timeouts** on I/O.
- Handle **asyncio.CancelledError** correctly.
- Pass static analysis: **MyPy** + **Ruff**.
- Complete type hints.
- Unit test coverage ~100%.

---

## ✅ Structured Guardrails

### 1️⃣ Enforce Async I/O

- Use only **async-capable** libraries:
  - HTTP → `httpx.AsyncClient`
  - Files → `aiofiles`
  - DB → `aiosqlite`, `asyncpg`, etc.
- Never call blocking libraries directly in async code.

**❌ Bad:**

~~~~python
async def load():
    data = requests.get("https://example.com")  # ❌ Blocking
    return data.text
~~~~

**✅ Good:**

~~~~python
import httpx

async def load():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
        return response.text
~~~~

---

### 2️⃣ Use TaskGroup for Concurrency

- All background tasks must be tracked.
- No "fire-and-forget" coroutines.
- Use Python 3.11+ `asyncio.TaskGroup`.

**Example:**

~~~~python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker1())
        tg.create_task(worker2())
~~~~

---

### 3️⃣ Graceful Cancellation

- Always handle `asyncio.CancelledError`.
- Clean up resources and re-raise to propagate.

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

### 4️⃣ Await All Subtasks

- Never return or ignore unawaited coroutines.
- Use `asyncio.shield()` to protect critical sections.

**Example:**

~~~~python
await asyncio.shield(save_important_data())
~~~~

---

### 5️⃣ Explicit Timeouts

- Always use **reasonable timeouts** on network/DB calls.

**Example:**

~~~~python
response = await client.get(url, timeout=5)
~~~~

---

### 6️⃣ Exception Handling

- Use try/except around expected errors.
- Log with **contextual info**.
- Avoid broad excepts that swallow tracebacks.

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

## ✅ 7️⃣ Safe Sync Integration

> For exceptional cases only!

- If you **must** use a blocking/sync library, always isolate in an executor.

**Example:**

~~~~python
import asyncio

def blocking_work(x: int) -> int:
    # Truly blocking logic
    ...

async def async_wrapper(x: int) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, blocking_work, x)
~~~~

✅ Document *why* sync is unavoidable.  
✅ Keep sync-wrapping isolated in dedicated modules.  
✅ Explicitly label as "SYNC EXCEPTION HANDLER" in codebase.

---

## ✅ Enforce Async File I/O

- Always use **aiofiles** in async def.
- Blocking built-in `open()` is prohibited.

**Example:**

~~~~python
import aiofiles

async def read_file(path: str) -> str:
    async with aiofiles.open(path, mode='r') as f:
        return await f.read()
~~~~

---

## ✅ Logging and Observability

- Use structured logging (e.g. JSON) with:
  - module
  - function
  - request_id
  - timestamp
  - level
- Consistent, clear log messages for:
  - task start/stop
  - errors
  - key events
- Prefer `logging` module or `structlog`.

---

## ✅ Static Analysis Requirements

- Must pass **MyPy** (type checking).
- Must pass **Ruff** (linting, formatting).
- Complete, consistent **type hints** everywhere.

---

## ✅ Testing Requirements

- Use **pytest** and **pytest-asyncio**.
- Write **unit tests in parallel** with production code.
- Target ~100% test coverage.
- Tests must be **minimal, clear, deterministic**.
- Use **AsyncMock** to isolate async dependencies.

**Example test:**

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

## ✅ Anti-Patterns (Strictly Forbidden)

- Fire-and-forget tasks not tracked.
- Blocking I/O in async functions.
- Broad `except:` without logging.
- Returning unawaited coroutines.
- Mixing sync calls without explicit wrapping.
- Missing type hints.

---

## ✅ Summary

- ✅ Async everywhere by default.
- ✅ Track all tasks with TaskGroup.
- ✅ Handle CancelledError correctly.
- ✅ Await all coroutines.
- ✅ Use shield for critical sections.
- ✅ Explicit timeouts on I/O.
- ✅ No blocking sync in async code without explicit wrapping.
- ✅ Enforce async file I/O with aiofiles.
- ✅ Structured logging.
- ✅ 100% type-hinted, static-analysed code.
- ✅ Full unit test coverage with pytest-asyncio.

---

> **AI Guardrail:** Never generate blocking sync code inside async functions unless you explicitly use `run_in_executor` and document why. Default = async everywhere.