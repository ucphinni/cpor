# Async Database Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, and testable async database code** in Python. These instructions **assume [aipy-core-instructions.md](aipy-core-instructions.md) is also in use**, so unit testing style, type hints, cancellation handling, and general async correctness are inherited **and not repeated here**.

---

## ✅ Priority: Correct, Minimal, Testable Async DB Code

- Always use **connection pools** for PostgreSQL.
- Use **async drivers**:
  - PostgreSQL: `asyncpg` (preferred), fallback `aiopg`.
- Always close cursors or use `async with` context managers.
- Use **explicit transactions** with `async with` blocks.
- Add **reasonable timeouts** for queries where applicable.

---

## ✅ PostgreSQL: Use asyncpg Driver

- Use an **asyncpg connection pool** for efficiency.
- Reuse connections instead of opening per query.
- Use **prepared statements** or **parameterized queries** to prevent SQL injection.
- Map rows explicitly to `dict(row)` or **dataclass** instances.
- Use transactions with:

~~~~python
async with conn.transaction():
    ...
~~~~

- Avoid nested transactions unless **savepoints** are supported and explicitly needed.
- Use **async generators** for streaming large result sets.
- Handle **asyncpg-specific exceptions** (e.g., `asyncpg.exceptions.PostgresError`).
- Never call **sync DB code** inside async functions.
- Always `await` async DB calls.

---

## ✅ Stored Procedures and Functions

- Prefer **stored procedures/functions** for complex DB logic.
- Use:

~~~~sql
CALL procedure_name(...)
~~~~
or
~~~~sql
SELECT function_name(...)
~~~~

- Explicitly handle output parameters and return values.
- Wrap related calls in **transactions** to maintain consistency.
- Write **unit tests** specifically exercising stored procedures.
- Document **assumptions and parameters** clearly.

---

## ✅ Connection Pooling and Resource Management

- Always use **connection pools** with PostgreSQL (`asyncpg.Pool`).
- Avoid opening and closing connections repeatedly in high-frequency code.
- Use:

~~~~python
async with pool.acquire() as conn:
    async with conn.transaction():
        ...
~~~~

- Always ensure **cursors** and connections are properly closed.

---

## ✅ Timeout Management

- Use explicit **query timeouts** to avoid hung queries.
- Set timeouts on **network calls**, **DB queries**, and **transactions** where supported.
- Handle **timeout exceptions** explicitly.
- Propagate errors for **retry** or **fallback** logic.
- Use conservative **default timeout values** (e.g., 3–5 seconds).

---

## ✅ Exception Handling and Logging

- Catch **specific database exceptions**:

~~~~python
asyncpg.exceptions
aiosqlite.Error
~~~~

- Log exceptions with **contextual information**.
- Avoid broad except clauses that swallow errors.
- Fail fast on critical errors, letting calling code **handle or retry**.
- Clean up resources using `async with` or in `finally` blocks.

---

## ✅ Async Generators for Large Result Sets

- Use **async generators** to process or stream large results **without loading everything at once**.
- Avoid `.fetchall()` on huge result sets.
- Example pattern:

~~~~python
async def stream_users(conn):
    async with conn.transaction():
        async for row in conn.cursor("SELECT * FROM users"):
            yield dict(row)
~~~~

---

## ✅ Unit Testing Async DB Code

- Use **pytest-asyncio** for async test functions.
- Use a **dedicated test database** or **mocks**.
- Mock DB calls with **AsyncMock** or simple fakes.
- Isolate DB code to enable focused unit tests.
- Aim for **100% test coverage** on the DB interaction layer.
- Clean up DB state between tests.

---

## ✅ AI-Guardrails: High-Risk Async DB Pitfalls (Ranked)

### 1. Result Shape / Mapping Clarity

- Always explicitly convert driver rows:

~~~~python
row = await conn.fetchrow(query, *params)
if row:
    result = dict(row)
~~~~

### 2. Cursor / Context Management

- Always use `async with`:

~~~~python
async with pool.acquire() as conn:
    async with conn.transaction():
        ...
~~~~

### 3. Connection Pooling Discipline

- Avoid new connections every query.
- Use pooled connections with `asyncpg.Pool`.

### 4. Transaction Nesting

- Don’t nest transactions unless **savepoints** are used.

### 5. Await Discipline

- Never return unawaited coroutines.
- Always `await` DB calls.

### 6. Timeout Discipline

- Always specify **timeouts** on DB operations.

### 7. Exception Handling Specificity

- Catch and handle **DB-specific** exceptions.

### 8. Resource Cleanup

- Use `async with` for connections and transactions.

### 9. Async Generators

- Stream large data sets to avoid memory issues.

### 10. Stored Procedure Usage

- Explicitly handle **output params** and **transactions**.

### 11. Mocking Async DB Calls in Tests

- Use **AsyncMock** for async DB functions.

### 12. Long-Lived vs Short-Lived Connections

- Use **pooled, short-lived** connections for PostgreSQL.

---

## ✅ Summary

- Use **asyncpg** with connection pools for PostgreSQL; fallback to `aiopg` if needed.  
- Explicitly **map query results** (e.g., `dict(row)`).  
- Manage transactions with `async with` context managers.  
- Use **async generators** for large data streaming.  
- Add **timeouts** and handle exceptions explicitly.  
- Write **unit tests** with **pytest-asyncio** and **AsyncMock**.  
- Maintain strict **await** discipline and **resource cleanup**.  
- Avoid nested transactions without savepoints.  
- Use **stored procedures** for complex logic and test them thoroughly.  
- Properly manage **connection pooling and reuse**.   