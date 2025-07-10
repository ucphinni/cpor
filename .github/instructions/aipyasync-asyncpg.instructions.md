# Async Database Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, and testable async database code** in Python. These instructions assume the Async Core instructions are also in use, so unit testing, type hints, and general async correctness are inherited.

---

## ✅ Priority: Correct, Minimal, Testable Async DB Code

- Read [Link to aipyasync-core.instructions.md](aipyasync-core.instructions.md)
- Always use connection pools for PostgreSQL.
- Use async drivers:  
  - PostgreSQL: `asyncpg` preferred, fallback `aiopg`.
- Always close cursors or use `async with` context managers.
- Use explicit transactions with `async with` blocks.
- Provide explicit type hints for query inputs and outputs.
- Add reasonable **timeouts** for queries where applicable.

---

## ✅ PostgreSQL: Use asyncpg Driver

- Use **asyncpg** connection pool for efficiency.
- Reuse connections instead of opening per query.
- Use prepared statements or parameterized queries to prevent SQL injection.
- Map rows explicitly: `dict(row)` or dataclass instances.
- Use transactions with `async with conn.transaction():`.
- Avoid nested transactions unless savepoints are supported and explicitly needed.
- Use async generators for streaming large query results.
- Handle asyncpg-specific exceptions (e.g., `asyncpg.exceptions.PostgresError`).
- Never call synchronous DB code inside async functions.
- Always `await` async DB calls.

---

## ✅ Stored Procedures and Functions

- Prefer using stored procedures or functions for complex DB logic when possible.
- Use `CALL procedure_name(...)` or `SELECT function_name(...)` depending on DB and driver.
- Explicitly handle output parameters and return values.
- Wrap multiple related calls in transactions to maintain consistency.
- Write unit tests specifically exercising stored procedure calls.
- Document assumptions and parameters clearly.

---

## ✅ Connection Pooling and Resource Management

- Always use connection pools with PostgreSQL (`asyncpg.Pool`).
- Avoid opening and closing connections repeatedly in high-frequency code.
- Use `async with pool.acquire()` to safely get and release connections.
- For SQLite, long-lived connections are acceptable since it’s file-based and single-user.
- Ensure cursors are closed properly, ideally via `async with`.

---

## ✅ Timeout Management

- Use explicit **query timeouts** to avoid hung queries.
- Set timeouts on network calls, DB queries, and transactions where driver supports.
- Handle timeout exceptions explicitly and propagate errors for retry or fallback.
- Use conservative default timeout values (e.g., 3–5 seconds) unless business logic demands more.

---

## ✅ Exception Handling and Logging

- Catch specific database exceptions (`asyncpg.exceptions`, `aiosqlite.Error`).
- Log exceptions with contextual information.
- Avoid broad except clauses that swallow exceptions.
- Fail fast on critical errors, allowing calling code to handle or retry.
- Clean up resources in `finally` blocks or using `async with`.

---

## ✅ Async Generators for Large Result Sets

- Use async generators to process or stream large query results without loading all at once.
- Avoid `.fetchall()` for huge data sets.
- Example pattern:

```
async def stream_users(conn):
    async with conn.transaction():
        async for row in conn.cursor("SELECT * FROM users"):
            yield dict(row)
```

---

## ✅ Unit Testing Async DB Code

- Use **pytest-asyncio** for async test functions.
- Use a dedicated test DB instance or mocks.
- Mock DB calls with **AsyncMock** or simple fakes.
- Isolate DB code to enable focused unit tests.
- Aim for **100% test coverage** on DB interaction layers.
- Clean up DB state between tests.

---

## ✅ AI-Guardrails: High-Risk Async DB Pitfalls (Ranked)

### 1. Result Shape / Mapping Clarity

- Always explicitly convert driver rows to dicts or models.
- Don’t assume rows are dicts by default.

```
row = await conn.fetchrow(query, *params)
if row:
    result = dict(row)
```

### 2. Cursor / Context Management

- Always use `async with` for connections and transactions.
- Not managing context properly leaks resources and causes bugs.

```
async with pool.acquire() as conn:
    async with conn.transaction():
        ...
```

### 3. Connection Pooling Discipline

- Avoid opening new connections every query.
- Use pooled connections with `asyncpg.Pool`.

### 4. Transaction Nesting

- Don’t nest transactions unless savepoints are supported and explicitly used.
- Nested transactions without savepoints lead to errors.

### 5. Await Discipline

- Never return unawaited coroutines.
- Always await DB calls and coroutines fully.

### 6. Timeout Discipline

- Always specify timeouts on DB operations where possible.
- Avoid hanging coroutines.

### 7. Exception Handling Specificity

- Catch and handle DB-specific exceptions explicitly.
- Avoid generic excepts swallowing tracebacks.

### 8. Resource Cleanup

- Use context managers (`async with`) for connections and transactions.
- Ensure cleanup even in case of cancellation or errors.

### 9. Async Generators

- Use async generators for large queries, avoid `.fetchall()` with huge data sets.

### 10. Stored Procedure Usage

- Explicitly handle output params and transactions when calling stored procedures.

### 11. Mocking Async DB Calls in Tests

- Use `AsyncMock` for async DB functions in unit tests.
- Always `await` mocked async calls in tests.

### 12. Long-Lived vs Short-Lived Connections

- For PostgreSQL, rely on pooled short-lived connections.
- Ensure proper acquisition and release.

---

## ✅ Summary

- Use **asyncpg** with connection pools for PostgreSQL; fallback to `aiopg` only if needed.  

- Explicitly map query results (e.g., `dict(row)`).  

- Manage transactions with `async with` context managers.  

- Use async generators for large data streaming.  

- Add query and transaction timeouts, handle exceptions explicitly.  

- Write unit tests with **pytest-asyncio** and **AsyncMock**.  

- Follow strict await discipline and context cleanup.  

- Avoid nested transactions without savepoints.  

- Use stored procedures for complex logic; test them thoroughly.  

- Properly manage connection pooling and reuse.  
  
  ---







# 
