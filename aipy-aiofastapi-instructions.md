Here’s the cleaned, production-ready version of your AsyncFastAPI Instructions, fully aligned with your aipy-core-instructions.md structure and mindset. It eliminates repetition, clarifies assumptions, and uses quadruple tildes for all code.


---

# AsyncFastAPI Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, production-ready FastAPI async code**. These instructions **assume [aipy-core-instructions.md](aipy-core-instructions.md) is also in use** — all async core behavior (e.g. `TaskGroup`, cancellation, shielding, type hints, pytest-asyncio) is inherited and **not repeated here**.

---

## ✅ Priority: Correct, Predictable, Idiomatic FastAPI

- Correctness first — **no shortcuts**.
- Use `async def` for **all route handlers**.
- Minimize business logic in endpoints — push logic into **service layers**.
- Use **Pydantic models** for input/output validation.
- Use **complete type hints** to improve clarity and model generation.

---

## ✅ Use FastAPI’s Dependency Injection

- Use `Depends()` to **inject services**, **DB sessions**, or **auth logic**.
- Dependencies must be:
  - Small
  - Stateless or scoped
  - Testable without mocks

**Example:**

~~~~python
from fastapi import Depends

async def get_service() -> Service:
    return Service()

@router.get("/items")
async def read_items(service: Service = Depends(get_service)):
    return await service.list_items()
~~~~

---

## ✅ Async Database Access (see database instructions)

- Use **async drivers only**:
  - Postgres: `asyncpg`
  - SQLite: `aiosqlite`
- Open connections using `async with`.
- Manage DB lifecycles using **FastAPI dependencies** or **lifespan**.

**Example (SQLite with dependency):**

~~~~python
async def get_db():
    async with aiosqlite.connect("db.sqlite") as db:
        yield db

@router.get("/users/{id}")
async def get_user(id: int, db = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE id=?", (id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else {}
~~~~

---

## ✅ Lifespan: Startup, Shutdown, and Background Tasks

Use **FastAPI's `lifespan` context manager** to:

- Initialize DB pools or background workers.
- Cleanly cancel background tasks on shutdown.
- Avoid starting background tasks elsewhere (e.g. decorators).

**Example pattern with TaskGroup:**

~~~~python
from contextlib import asynccontextmanager
from fastapi import FastAPI

async def periodic_task():
    try:
        while True:
            await do_work()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        await cleanup()
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with asyncio.TaskGroup() as tg:
        tg.create_task(periodic_task())
        yield
        # TaskGroup auto-cancels on exit

app = FastAPI(lifespan=lifespan)
~~~~

---

## ✅ Serving with Hypercorn in Production

- Use **Hypercorn** as your ASGI server.
- Prefer `uvloop` workers for performance (if compatible).
- Bind to **0.0.0.0** on production port (e.g., 8000).
- Set **worker count** according to CPU cores.

**Example command:**

~~~~bash
hypercorn app.main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvloop
~~~~

---

## ✅ Reverse Proxy with Caddy

- Expect **Caddy** or similar to:
  - Terminate TLS
  - Handle HTTP/3 (QUIC)
  - Perform compression and static serving
- Backend app should **only serve HTTP/1.1 or HTTP/2**.
- Let proxy handle **TLS, caching, logging, compression, headers**.

---

## ✅ Route Design and Clean Response Models

- Use **Pydantic models** for both input and output.
- Always declare `response_model` and `status_code`.
- Only return **JSON-serializable data**.
- Avoid in-route I/O or logic unless trivial.

**Example:**

~~~~python
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    name: str

@router.get("/users/{id}", response_model=UserOut, status_code=200)
async def get_user(id: int):
    user = await service.get_user(id)
    return user
~~~~

---

## ✅ Testing FastAPI Async Routes

- Use **pytest-asyncio** for test functions.
- Use **httpx.AsyncClient** to make test requests.
- Avoid FastAPI’s `TestClient` (sync-only).
- Mock external I/O (e.g. DB) using **AsyncMock**.
- Keep tests **focused, fast, and deterministic**.

**Example:**

~~~~python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_read_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/1")
        assert response.status_code == 200
~~~~

---

## ✅ AI Guardrails: Common Mistakes to Avoid

- ❌ Do not use **blocking** DB or HTTP clients in `async def`.
- ✅ Use **async dependencies** and `async with` for all I/O.
- ❌ Do not launch `asyncio.create_task()` directly in route handlers.
- ✅ Use `TaskGroup` via **lifespan**, not ad-hoc.
- ✅ Always re-raise `CancelledError` after cleanup.
- ✅ Always use **type hints** and **Pydantic validation**.
- ✅ Avoid deeply nested control flow in route logic.

---

## ✅ Summary

- Routes are **pure async**, short, and type-safe.
- Use **FastAPI dependency injection** to isolate I/O and logic.
- Run **Hypercorn** behind **Caddy** in production.
- Use **lifespan** to manage app-wide resources and tasks.
- Write **tests using pytest-asyncio** and **httpx.AsyncClient**.
- Never block the event loop or forget to `await`.
- All FastAPI code depends on and follows the patterns in [aipy-core-instructions.md](aipy-core-instructions.md).


---

Highlights:

✅ No repetition of core TaskGroup, cancellation, or timeout behavior
✅ Uses FastAPI’s lifespan, DI, and Pydantic models correctly
✅ Clean async testing with httpx.AsyncClient
✅ All code blocks are quadruple tildes
✅ Clean section separation, no bloat, no sync leakage

Let me know if you want a variant that’s SQLite-only or Postgres-only focused!

