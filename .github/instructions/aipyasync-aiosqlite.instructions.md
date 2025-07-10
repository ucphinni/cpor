# Async Database Instructions (SQLite) for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, and testable async SQLite database code** in Python. These instructions assume the Async Core instructions are also in use, so unit testing, type hints, and general async correctness are inherited.

---

## ✅ Priority: Correct, Minimal, Testable Async DB Code

- Read [Link to aipyasync-core.instructions.md](aipyasync-core.instructions.md)
- Use **aiosqlite** as the preferred async SQLite driver.
- Always close cursors or use `async with` context managers.
- Use explicit transactions with `async with` blocks.
- Provide explicit type hints for query inputs and outputs.
- Add reasonable **timeouts** for queries where applicable.

---

## ✅ SQLite: Use aiosqlite Driver

- Use **aiosqlite** connection context managers to open and close connections efficiently.
- Use `async with aiosqlite.connect(...)` for connection lifecycle.
- Use `async with conn.execute(...)` for queries.
- Use transactions with `async with conn.transaction()` or explicit `BEGIN/COMMIT` commands.
- Always commit changes explicitly with `await conn.commit()` when modifying data.
- Map rows explicitly using `dict(row)` by enabling `row_factory`.

**Example:**

```
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
```

---

## ✅ Stored Procedures and Functions (SQLite Context)

- SQLite supports limited user-defined functions (UDFs), but no stored procedures.
- Complex logic should be handled in application code, not DB.
- Use SQLite functions and triggers sparingly.
- Document any use of triggers or UDFs carefully.
- Write tests covering all DB interactions and logic.

---

## ✅ Connection and Resource Management

- Open and close connections efficiently using async context managers.
- Avoid holding connections open longer than necessary.
- Always close cursors properly using `async with` blocks.
- Use connection pooling only if implemented outside (e.g., via external tools) — `aiosqlite` does not provide pooling.

---

## ✅ Timeout Management

- SQLite via aiosqlite does not natively support query timeouts.
- Implement external timeout logic if needed via `asyncio.wait_for()`.
- Be cautious with long-running queries blocking the event loop.

---

## ✅ Exception Handling and Logging

- Catch `aiosqlite.Error` and related exceptions explicitly.
- Log with context, avoid swallowing exceptions.
- Fail fast on unrecoverable errors.
- Use `try/except` blocks around DB calls as needed.

---

## ✅ Async Generators for Large Result Sets

- Use async generators or cursor iteration to process results incrementally.
- Avoid reading large query results fully into memory.

**Example:**

```
async def stream_users(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            async for row in cursor:
                yield dict(row)
```

---

## ✅ Unit Testing Async DB Code

- Use **pytest-asyncio** for async test functions.
- Use a separate test SQLite DB file or in-memory DB.
- Use fixtures to setup/teardown DB state between tests.
- Mock DB calls if needed with **AsyncMock**.
- Keep tests minimal, clear, and deterministic.
- Aim for **100% test coverage** on DB layers.

---

## ✅ AI-Guardrails: High-Risk Async DB Pitfalls (Ranked)

### 1. Explicit Row Mapping

- Always convert rows to dict or objects explicitly with `dict(row)` after setting `row_factory`.

### 2. Context Management

- Use `async with` for connections and cursors to ensure cleanup.

### 3. Commit Discipline

- Always call `await conn.commit()` after write operations.

### 4. Await Discipline

- Never forget to `await` async DB calls.

### 5. Exception Handling

- Catch and handle `aiosqlite.Error` explicitly.

### 6. Resource Management

- Close connections and cursors promptly.

### 7. Async Iteration

- Use async iteration over cursors for large datasets.

### 8. Timeout Awareness

- Use `asyncio.wait_for()` externally if needed.

### 9. Test DB Setup

- Use isolated DB files or in-memory DB for tests.

### 10. Mocking Async DB Calls

- Use `AsyncMock` in tests and always await mocks.

---

## ✅ Summary

- Use **aiosqlite** with async context managers for SQLite access.  
- Set `row_factory` to `aiosqlite.Row` and convert rows explicitly.  
- Commit transactions explicitly with `await conn.commit()`.  
- Use async generators to stream large results.  
- Handle exceptions and close resources carefully.  
- Write full **pytest-asyncio** tests with fixtures and mocks.  
- Always `await` async calls.  
- Timeout handling is external via `asyncio.wait_for()`.  
- Complex logic should stay out of DB (SQLite lacks stored procs).  
- Ensure clear type hints and consistent async patterns.  
