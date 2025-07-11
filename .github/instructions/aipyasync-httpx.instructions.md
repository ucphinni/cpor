> **IMPORTANT**  
> DO NOT MODIFY THIS FILE UNLESS IN STRUCTURED REVIEW.  
> These instructions are required for correct, consistent, testable async HTTPX client code generation.  

# HTTPX Async Client Instructions for GitHub Copilot Chat

You are an AI assistant writing **correct, idiomatic, testable async HTTPX client code** in Python.  
These instructions **assume [aipyasync-core.instructions.md](aipyasync-core.instructions.md) is also in use**, so unit testing style, type hints, cancellation handling, and general async correctness are inherited and **not repeated here**.

---

## ✅ Priority: Correct, Minimal, Testable Async Code

- Prioritize **correctness** over terseness.
- Avoid blocking the event loop.
- Use **async/await** idioms consistently.
- Always close resources using **context managers**.
- Add **reasonable timeouts** for HTTP requests.

---

## ✅ Session Management Strategy

- Use **httpx.AsyncClient** for all HTTP calls.
- Avoid creating multiple clients unnecessarily.
- **DO NOT** create a client at module-level scope (no singletons/globals).
- Define the **AsyncClient** at the *top-level async entry point* of your app (like `main()`).
- Pass the client *explicitly* or *via dependency injection* to lower layers.
- Use `async with` to ensure client cleanup.

---

## ✅ Recommended Pattern

Define and manage client lifecycle at the top level:

~~~~python
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        await run_business_logic(client)
~~~~

Pass `client` down or inject into your classes/services:

~~~~python
async def run_business_logic(client: httpx.AsyncClient):
    await do_stuff(client)
~~~~

---

## ✅ Connection Pooling Guidance

- The AsyncClient manages connection pooling automatically.
- Keep it alive for the entire app session via **async with** at top-level.
- Avoid re-creating the client repeatedly for each request.
- No explicit singleton/global pattern—use DI instead.

---

## ✅ Context Propagation Example

Use **dependency injection** or explicit parameters:

~~~~python
class MyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def fetch_data(self, url: str) -> dict:
        response = await self.client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
~~~~

---

## ✅ Exception Handling

- Always use **response.raise_for_status()** to detect errors.
- Catch **httpx.RequestError** for network-level issues.
- Catch **httpx.HTTPStatusError** for 4xx/5xx responses if needed.
- Use **try/except** to handle and log errors meaningfully.

---

## ✅ Timeout Management

- Always specify a **timeout** in calls:

~~~~python
await client.get(url, timeout=10)
~~~~

- Consider using a default timeout on client:

~~~~python
httpx.AsyncClient(timeout=10)
~~~~

---

## ✅ Type Hint Discipline

- Explicitly annotate functions with:

~~~~python
async def fetch_data(self, url: str) -> dict:
    ...
~~~~

- Use **Optional** and **Union** when needed.

---

## ✅ Unit Testing with pytest-asyncio

- Use **pytest-asyncio** for async test functions.
- Use **httpx.MockTransport** or **respx** for mocking:

~~~~python
import respx

@respx.mock
async def test_fetch_data():
    route = respx.get("https://example.com/").mock(return_value=httpx.Response(200, json={"key": "value"}))
    async with httpx.AsyncClient() as client:
        result = await fetch_data(client, "https://example.com/")
        assert result == {"key": "value"}
~~~~

- Keep tests clear, minimal, and deterministic.

---

## ❌ Anti-Patterns

- Creating or using a global `AsyncClient` singleton at module scope.
- Forgetting to call `response.raise_for_status()` on responses.
- Executing HTTP calls without timeouts or context managers.
- Mixing sync HTTP libraries (e.g., `requests`) inside async functions.

## 🛠 Logging and Observability

- Log each HTTP request and response: `method`, `url`, `status_code`, `duration_ms`.
- Capture and log HTTP error details including status code and response body.
- Use structured logs for easier aggregation and tracing.

## 💡 Configuration Examples

```python
import httpx

client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))
```

```python
from fastapi import Depends

def get_http_client() -> httpx.AsyncClient:
    return client
```

---

## ✅ AI-Guardrails: High-Risk HTTPX Async Client Pitfalls (Ranked)

### 1. Global Singleton Client

❌ Avoid at module scope.
✅ Define client at top-level async function.

### 2. Forgetting `async with`

❌ Never skip context manager.
✅ Use `async with` for client lifecycle.

### 3. Ignoring Exceptions

❌ Never ignore errors.
✅ Use `raise_for_status()` and handle exceptions.

### 4. No Timeouts

❌ Avoid no-timeout calls.
✅ Always specify timeouts.

### 5. Recreating Clients Excessively

❌ Avoid new client per request.
✅ Reuse one client during app session.

### 6. Implicit Dependencies

❌ Don’t use hidden globals.
✅ Pass client explicitly or via DI.

### 7. Blocking Calls

❌ Don’t use sync methods in async code.
✅ Always await HTTP calls.

---

## ✅ Summary

- Use **httpx.AsyncClient** with **async with** at the top level.  
- Avoid module-level singletons.  
- Manage client lifespan explicitly.  
- Pass client to lower layers or services.  
- Handle exceptions carefully.  
- Enforce timeouts.  
- Add full **pytest-asyncio** tests with mocks (e.g. respx).  
- Keep type hints and async idioms consistent.