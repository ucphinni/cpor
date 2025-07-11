# AsyncFastAPI Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, production-ready FastAPI async code** designed for **accuracy on the first try**. These instructions layer on top of **AsyncCore** instructions — **do not repeat AsyncCore** patterns, but assume they are in effect.

---

## ✅ Priority: Correct, Predictable, Idiomatic FastAPI

- Read [Link to aipyasync-core.instructions.md](aipyasync-core.instructions.md)
- Always use **FastAPI’s async request handlers** (`async def`).
- Minimize business logic in route functions.
- Validate inputs with **Pydantic models**.
- Add **type hints everywhere** — this aids the AI in understanding intent.
- Keep route handlers **short** and **readable**.
- Split pure logic into **separate service modules**.

---

## ✅ Use FastAPI’s Dependency Injection

- Define **explicit dependencies** with `Depends()`.
- Keep dependencies **small**, **pure**, and **easy to test**.
- Dependencies should not have side-effects outside their scope.
- Use them to **inject services**, **DB sessions**, **auth**, etc.

**Example:**

```
from fastapi import Depends

async def get_service() -> Service:
    return Service()

@router.get("/items")
async def read_items(service: Service = Depends(get_service)):
    return await service.list_items()
```

---

## ✅ Async Database Access Patterns

- Always use **async libraries**:
  - **aiosqlite** for SQLite.
  - **asyncpg** for Postgres.
- Manage connections via **FastAPI lifespan** events or **dependency scopes**.
- Use **async with** for connection and transaction lifetimes.
- Avoid global connections — pass them explicitly.

**Example with aiosqlite:**

```
async def get_db():
    async with aiosqlite.connect("db.sqlite") as db:
        yield db

@router.get("/users/{id}")
async def get_user(id: int, db = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE id=?", (id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else {}
```

---

## ✅ Serving with Hypercorn (Production-Ready)

- Assume **Hypercorn** as ASGI server.
- Prefer **uvloop** worker class if compatible.
- Bind to **0.0.0.0** with a production port.
- Set **worker count** based on CPU.
- Don’t run with FastAPI’s dev server in production.

**Example command:**

```
hypercorn app.main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvloop
```

---

## ✅ Caddy or Reverse Proxy Frontend

- Assume **Caddy** terminates TLS and handles HTTP/3.
- Backend FastAPI app **targets HTTP/1.1 or HTTP/2** only.
- Avoid implementing custom QUIC/HTTP/3 logic in-app.
- Let the reverse proxy handle compression, TLS, and static assets.

---

## ✅ Lifespan Events for Startup and Shutdown

- Use **FastAPI lifespan** to manage startup and shutdown.
- Initialize resources on **startup** (DB pools, clients, etc.).
- Close resources on **shutdown**.
- Ensure **clean task cancellation**.

**Example pattern:**

```
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with asyncio.TaskGroup() as tg:
        app.state.taskgroup = tg
        yield
        tg.cancel_scope.cancel()
        await tg.wait_closed()

app = FastAPI(lifespan=lifespan)
```

---

## ✅ Background Async Tasks Using TaskGroup

- Avoid FastAPI’s sync-only `BackgroundTasks` for async work.
- Use **TaskGroup** to manage async background jobs.
- Keep task group **open during app lifetime** via lifespan.
- Always **await or cancel** background tasks cleanly on shutdown.
- Avoid decorators for periodic jobs — use explicit loops with `asyncio.sleep`.

**Example pattern:**

```
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
        # TaskGroup will automatically cancel on exit
```

---

## ✅ Testing FastAPI Async Routes

- Use **pytest-asyncio** for async test functions.
- Use **httpx.AsyncClient** for making test HTTP calls.
- Don’t use FastAPI’s sync TestClient for async routes.
- Test **minimal** endpoints and **validation** separately.
- Mock DB calls or service layer with **AsyncMock**.

**Example:**

```
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_read_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/1")
        assert response.status_code == 200
```

---

## ✅ Clean, Idiomatic FastAPI

- Use **Pydantic models** for request/response validation.
- Explicitly define **status codes** in route decorators.
- Add **response_model** for docs and validation.
- Return **JSON-serializable** objects only.
- Avoid complex side effects in route functions.

**Example:**

```
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    name: str

@router.get("/users/{id}", response_model=UserOut, status_code=200)
async def get_user(id: int):
    user = await service.get_user(id)
    return user
```

---

## ❌ Anti-Patterns

- Putting business logic directly in route handlers instead of service modules.
- Starting background tasks outside of the FastAPI lifespan context.
- Using FastAPI’s sync TestClient for async routes.
- Swallowing `CancelledError` or other critical exceptions in dependencies or routes.

## 🛠 Logging and Observability

- Log each incoming request with method, path, and request ID.
- Log response status and duration as structured data.
- Use FastAPI middleware for centralized logging and error handling.

## 💡 Configuration Examples

```yaml
# config.yaml
database:
  dsn: "postgresql://user:pass@localhost/db"
http:
  host: "0.0.0.0"
  port: 8000
```

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    dsn: str
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
```

---

## ✅ Summary

- **Accurate, testable FastAPI async code**.
- Routes are **pure async** with clear responsibilities.
- Use **dependencies** to inject services.
- Use **async DB drivers** with context managers.
- Manage background work via **TaskGroup** in lifespan.
- Serve with **Hypercorn** behind **Caddy** for production.
- Avoid blocking calls in async code.
- Test with **pytest-asyncio** and **httpx.AsyncClient**.
- Always use **type hints** for correctness and AI understanding.
