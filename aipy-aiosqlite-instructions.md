# Async Database Instructions (SQLite) for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, and testable async SQLite database code** in Python. These instructions **assume [aipy-core-instructions.md](aipy-core-instructions.md) is also in use**, so unit testing style, type hints, cancellation handling, and general async correctness are inherited **and not repeated here**.

---

## ✅ Priority: Correct, Minimal, Testable Async DB Code

- Prioritize **correctness** and **testability**.
- Use **async/await** idioms consistently.
- Avoid blocking the event loop.
- Use **aiosqlite** as the preferred async SQLite driver.
- Always close cursors or use `async with` context managers.
- Use **explicit transactions** with `async with` blocks.
- Provide **explicit type hints** for query inputs and outputs.
- Write **unit tests** with **pytest-asyncio** alongside code.
- Add **reasonable timeouts** for queries where applicable.

---

## ✅ SQLite: Use aiosqlite Driver

- Use **aiosqlite connection context managers** to open and close connections efficiently.
- Use:

~~~~python
async with aiosqlite.connect(...) as db:
    ...
~~~~

- Use:

~~~~python
async with db.execute(...) as cursor:
    ...
~~~~

- For transactions, use:

~~~~python
await db.execute("BEGIN")
# or
async with db.transaction():
    ...
~~~~

- Always **commit changes explicitly**:

~~~~python
await db.commit()
~~~~

- Enable `row_factory` and **map rows explicitly**:

~~~~python
db.row_factory = aiosqlite.Row
~~~~

**Example:**

~~~~python
import aiosqlite
from typing import Optional, Dict

async def get_user_by_id(db_path: str, user_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
~~~~

---

## ✅ Stored Procedures and Functions (SQLite Context)

- SQLite supports **limited user-defined functions (UDFs)** but no stored procedures.
- Complex logic should stay in **application code**, not in the DB.
- Use **SQLite functions and triggers sparingly**.
- Document any use of **triggers** or **UDFs** carefully.
- Write tests covering all DB interactions and **business logic**.

---

## ✅ Connection and Resource Management

- Open and close connections efficiently using **async context managers**.
- Avoid holding connections open longer than necessary.
- Always close cursors properly using `async with` blocks.
- Connection pooling is not built-in; if needed, implement externally.

---

## ✅ Timeout Management

- **aiosqlite** does not natively support query timeouts.
- Implement **external timeout logic** via `asyncio.wait_for()`:

~~~~python
await asyncio.wait_for(db.execute(...), timeout=5)
~~~~

- Be cautious with long-running queries blocking the event loop.

---

## ✅ Exception Handling and Logging

- Catch **aiosqlite.Error** and related exceptions explicitly.
- Log exceptions with **context** to aid debugging.
- Avoid broad excepts that swallow tracebacks.
- Fail fast on unrecoverable errors.
- Use `try/except` blocks around DB calls as needed.

---

## ✅ Async Generators for Large Result Sets

- Use **async generators** or cursor iteration to process large results incrementally.
- Avoid reading large query results fully into memory.

**Example:**

~~~~python
async def stream_users(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            async for row in cursor:
                yield dict(row)
~~~~

---

## ✅ Unit Testing Async DB Code

- Use **pytest-asyncio** for async test functions.
- Use a **separate test SQLite DB file** or **in-memory DB**:

~~~~python
":memory:"
~~~~

- Use **fixtures** to setup/teardown DB state between tests.
- Mock DB calls if needed with **AsyncMock**.
- Keep tests **minimal, clear, and deterministic**.
- Aim for **100% test coverage** on the DB layer.

---

## ✅ AI-Guardrails: High-Risk Async DB Pitfalls (Ranked)

### 1. Explicit Row Mapping

- Always convert rows to dicts or objects with:

~~~~python
dict(row)
~~~~

### 2. Context Management

- Use `async with` for connections and cursors to ensure cleanup.

### 3. Commit Discipline

- Always call:

~~~~python
await conn.commit()
~~~~

after write operations.

### 4. Await Discipline

- Never forget to **await** async DB calls.

### 5. Exception Handling

- Catch and handle **aiosqlite.Error** explicitly.

### 6. Resource Management

- Close connections and cursors promptly with **async with**.

### 7. Async Iteration

- Use **async iteration** over cursors for large datasets.

### 8. Timeout Awareness

- Use `asyncio.wait_for()` externally if needed.

### 9. Test DB Setup

- Use isolated DB files or **in-memory DB** for tests.

### 10. Mocking Async DB Calls

- Use **AsyncMock** in tests and always **await** mocks.

---

## ✅ Summary

- Use **aiosqlite** with **async context managers** for SQLite access.  
- Set **row_factory** to `aiosqlite.Row` and convert rows explicitly.  
- Commit transactions explicitly with **await conn.commit()**.  
- Use **async generators** to stream large results.  
- Handle **exceptions** and close resources carefully.  
- Write full **pytest-asyncio** tests with **fixtures and mocks**.  
- Always **await** async calls.  
- Timeout handling is external via **asyncio.wait_for()**.  
- Keep complex logic in **application code** (SQLite lacks stored procedures).  
- Ensure **clear type hints** and consistent **async patterns**.