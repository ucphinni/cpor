# Async Coding Instructions for GitHub Copilot Chat

You are an AI assistant that writes **simple, clean, minimal, and correct Python async code** focused on **ease of testing, readability, and correctness on first try**. These instructions layer onto the general instructions without repeating them unnecessarily, but they must remain **compatible** with them.

---

## 🚀 Priority: Correct, Simple, and Testable Async Code

- read the [Link to copilot_python_instructions.md](copilot_python_instructions.md)

---

## ✅ Asynchronous Python Patterns

- Use **async/await** consistently.
- Prefer `asyncio.create_task()` for concurrent work.
- Use `asyncio.TaskGroup` (Python 3.11+) to manage related tasks together.
- For Python <3.11, emulate TaskGroup with `asyncio.gather()`.
- Use `async with` for async context managers (like clients, files).
- Cleanly handle cancellation via `asyncio.CancelledError`.
- Always ensure all tasks are cancelled or awaited before shutdown.

**Example of TaskGroup-style concurrency:**

```
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker1())
        tg.create_task(worker2())
```

## ✅ TaskGroup Pattern for Background Work

- Prefer **TaskGroup.create_task()** over `asyncio.create_task()` for managing background tasks in modern Python.
- Construct the **TaskGroup** at the top-level `async main()` or pass it into classes or functions as needed.
- This ensures **structured concurrency**, where tasks are scoped, cancellable, and cleaned up on shutdown.
- For Python <3.11, you can emulate this pattern with `asyncio.gather()`.

**Example:**

```
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker1())
        tg.create_task(worker2())
```

---

## ✅ Structured Async Error Handling

- Always use **try/except** around awaits that can fail.
- Log errors consistently (use `logging` module).
- Gracefully handle `asyncio.CancelledError` separately when needed.
- Avoid swallowing exceptions without reporting.

**Example:**

```
import logging

async def process_item(item):
    try:
        await do_work(item)
    except asyncio.CancelledError:
        logging.info("Task was cancelled cleanly.")
        raise
    except Exception as e:
        logging.error(f"Error processing item: {e}")
```

---

## ✅ Connection Pooling and Resource Reuse

- Use **connection pools** for databases (e.g., `aiopg.create_pool`).
- Reuse **httpx.AsyncClient** instead of recreating it per request.
- Share connections with FastAPI dependencies or app state.

**Example:**

```
async with aiopg.create_pool(dsn) as pool:
    async with pool.acquire() as conn:
        ...
```

**Example with httpx:**

```
client = httpx.AsyncClient()

async def fetch_url(url: str):
    response = await client.get(url)
    return response.text
```

---

## ✅ FastAPI Lifespan Events (Recommended over @app.on_event)

- Prefer **lifespan context managers** in FastAPI 0.95+ for setup/teardown.
- AI should generate **new style** lifespan patterns.

**Example:**

```
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()

app = FastAPI(lifespan=lifespan)
```

---

## ✅ Advanced Concurrency Patterns

- Use `asyncio.Semaphore` to limit concurrency.
- Use `asyncio.Queue` for producer-consumer patterns.
- Avoid unbounded task spawning.

**Example with Semaphore:**

```
semaphore = asyncio.Semaphore(5)

async def limited_task():
    async with semaphore:
        await do_work()
```

**Example with Queue:**

```
queue = asyncio.Queue()

async def producer():
    for item in items:
        await queue.put(item)

async def consumer():
    while True:
        item = await queue.get()
        await process(item)
        queue.task_done()
```

---

## ✅ Backpressure and Rate-Limiting

- AI should generate patterns that avoid flooding external services.
- Use rate limiters or semaphores to manage outgoing request volume.

**Example:**

```
import asyncio

rate_limiter = asyncio.Semaphore(10)

async def limited_request():
    async with rate_limiter:
        await make_request()
```

---

## ✅ Custom Async Context Managers

- AI should know how to define and use them.
- Keeps resource acquisition/release clear and testable.

**Example:**

```
class MyResource:
    async def __aenter__(self):
        await open_resource()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await close_resource()

async with MyResource() as res:
    await res.use()
```

---

## ✅ Logging Best Practices

- Avoid print in production async code.
- Use structured logging.
- Include context like task ID or request ID when possible.

**Example:**

```
import logging

logger = logging.getLogger(__name__)

async def handler():
    logger.info("Handling request")
    try:
        await do_work()
    except Exception as e:
        logger.error("Failed to handle request", exc_info=e)
```

---

## ✅ Virtual Environment and Dependency Management

- Always assume **virtualenv** is active.
- Use **uv** to install packages for speed.
- Provide requirements with **requirements.txt** or **pyproject.toml**.

**Example Command:**

```
uv pip install -r requirements.txt
```

**Example requirements.txt:**

```
fastapi
hypercorn
httpx
aiosqlite
aiopg
aiofiles
pytest
pytest-asyncio
pytest-cov
```

---

## ✅ Coverage and CI Recommendations

- Use **pytest-cov** for coverage reports.
- Integrate tests into **CI/CD** pipelines.
- Ensure minimal coverage thresholds are enforced.

**Example command:**

```
pytest --cov=your_module tests/
```

---

## ✅ Typing for Async Generators and Streaming

- Use correct type hints for async generators.

**Example:**

```
from collections.abc import AsyncGenerator

async def line_reader(file) -> AsyncGenerator[str, None]:
    async for line in file:
        yield line
```

---

## ✅ Testing Async Code with Pytest

- Use **pytest-asyncio** for testing `async def`.
- Always provide **minimal clear unit tests**.
- Use **AsyncMock** for mocking async functions.
- Organize test files alongside source modules.
- Run tests under virtualenv with `pytest`.

**Example:**

```
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_data():
    mock_fetch = AsyncMock(return_value={"key": "value"})
    data = await mock_fetch("http://example.com")
    assert data == {"key": "value"}
```

---

## ✅ Testing FastAPI Async Routes

- Use **pytest-asyncio** for async test functions.
- Use **httpx.AsyncClient** for making test HTTP calls.
- Use FastAPI's built-in TestClient only for sync tests; prefer httpx for async.

**Example:**

```
import pytest
from httpx import AsyncClient
from myapp import app

@pytest.mark.asyncio
async def test_get_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/1")
        assert response.status_code == 200
```

---

## ✅ Avoid Mixing Sync and Async Code

- Never call blocking sync functions inside `async def`.
- Use fully async equivalents (`aiofiles`, `httpx`, `aiosqlite`).
- Avoid defeating concurrency by blocking the event loop.

**Bad (sync inside async):**

```
async def fetch():
    data = requests.get("https://example.com")  # ❌ Blocking!
    return data.text
```

**Good (fully async):**

```
import httpx

async def fetch():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
        return response.text
```

---

## ✅ Event Loop and Application Shutdown

- Cleanly close resources on shutdown.
- Use FastAPI `lifespan` or `@app.on_event("shutdown")`.
- Avoid global background tasks not tied to lifecycle.

**Example:**

```
@app.on_event("shutdown")
async def cleanup():
    await db_pool.close()
    logger.info("App shutdown complete.")
```

---

## ✅ Async Application Lifecycle (AI Reference)

1. **Startup**
   - Initialize resources (`aiosqlite`, `httpx`, etc.)
   - Start background tasks (`TaskGroup`)
2. **Request Handling**
   - Pure logic first
   - Async I/O last
   - Always use `async with`
3. **Shutdown**
   - Cancel background tasks
   - Flush logs
   - Close DB connections

---

## ✅ AI Guardrails: Common Async Mistakes to Avoid

- ✅ Always use `await` with coroutines.
- ❌ Never return un-awaited coroutines from `async def`.
- ✅ Use `async with` for async resources.
- ❌ Avoid `.result()` or `.run_until_complete()` in async code.
- ✅ Use `tg.create_task()` for background work.  tg symbol is constructed at the top level async main function or has been passed into an object while still in scope.

---

## ✅ Clean, Minimal, Idiomatic Async Expressions

- Use Pythonic short expressions.
- Avoid redundant `if/else` when returning booleans.
- Use clear variable names.
- Avoid unnecessary verbosity or punctuation.

**Verbose (to avoid):**

```
if is_valid:
    return True
else:
    return False
```

**Concise (preferred):**

```
return is_valid
```

---

## ✅ FastAPI with Hypercorn and Caddy Frontend

- Assume **Caddy** in front for TLS and HTTP/3 termination.
- Target HTTP/1.1 or HTTP/2 in backend FastAPI+Hypercorn.
- Avoid implementing custom QUIC server logic unless truly needed.

**Example Command:**

```
hypercorn myapp:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvloop
```

---

## ✅ Summary

- Use **pure async functions** where possible.
- Use **early returns / guard clauses** to simplify logic.
- Favor **TaskGroup** for clean concurrent tasks.
- Use **aiofiles**, **aiosqlite**, **aiopg**, **httpx**.
- Write **pytest** tests with **pytest-asyncio**.
- Cleanly shut down resources.
- Keep code clear, minimal, and idiomatic.
- Avoid blocking sync calls in async contexts.
- Use **FastAPI** + **Hypercorn** behind **Caddy** for production.
- Use **structured error handling**, **connection pooling**, and **advanced concurrency controls**.
- Follow **AI guardrails** to avoid common mistakes and ensure correctness **on first try**.
