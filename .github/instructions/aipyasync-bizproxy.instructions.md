# BusinessProxy Instructions for GitHub Copilot Chat

You are an AI assistant writing **a BusinessProxy abstraction layer** in Python for asynchronous systems.  

This document defines **the interface, responsibilities, and rules** for implementing a BusinessProxy that mediates between business logic and low-level transport details (e.g., HTTPX, FastAPI).  

It is intended for **clean, production-ready, testable code** with pluggable transport and error-handling strategies.

---

## ✅ Inherits Async Core

> ⚠️ Follow the [AsyncCore Instructions](async_core_instructions.md) for **all async correctness**, **I/O avoidance**, **TaskGroup management**, **cancellation handling**, and **test patterns**.  
>  
> This document does not repeat those rules but assumes full compliance.

---

## ✅ Purpose

- Encapsulate **transport details** (e.g., HTTPX, FastAPI).
- Expose a **clean async interface** to business logic:
  - `connect()`
  - `send()`
  - `receive()`
  - `close()`
- Hide retry, rate limit, encryption, and connection details behind the abstraction.

---

## ✅ Interface Shape

Your BusinessProxy must implement:

~~~~
class BusinessProxyProtocol:
    async def connect(self) -> None: ...
    async def send(self, message: Any, *, tags: Optional[List[str]] = None) -> None: ...
    async def receive(self) -> Any: ...
    async def close(self) -> None: ...
~~~~

✅ Notes:
- `tags` parameter supports optional **message tagging** for routing, rate limits, and priority.
- Implementations must remain **transport-agnostic** to business logic.

---

## ✅ Pluggable Transports

- Proxy must support **pluggable backends**:
  - e.g., HTTPX, FastAPI, WebSocket.
  - Plug-in approach must allow **easy swapping** without changing business logic.
- Use **dependency injection** or **factory patterns** for instantiation.

---

## ✅ Optional Plugins and Middleware

- Design for **middleware patterns**:
  - Rate limiting
  - Encryption/signature verification
  - Retry policies
  - Logging/auditing
- Middleware must be pluggable without modifying core proxy logic.

---

## ✅ Rate Limiting Support

- The proxy should **optionally** integrate rate limiting middleware.
- Support **multi-dimensional rate limits**:
  - Example: 100 calls/hour AND 5 calls/minute.
  - Enforce **all** dimensions (AND logic).
- Allow **tag-based** quotas:
  - Certain tagged messages count against certain quotas.
  - Others can be exempt or have separate limits.

---

## ✅ Retry Logic

- Provide **configurable retry strategies** for transient failures:
  - Exponential backoff.
  - Max retries.
  - Timeout ceilings.
- Retries should be **invisible** to business logic if successful.
- Expose **exhausted retries** as clear exceptions.

---

## ✅ Message Tagging

- `send()` and `receive()` must support **tags**:
  - Used for rate limiting.
  - Routing to appropriate middleware or queues.
  - Logging/auditing classifications.

✅ Examples:
~~~~
await proxy.send(message, tags=["priority:high", "service_call"])
~~~~

---

## ✅ Configuration

- Proxy should support **config injection**:
  - Project name
  - Transport selection
  - Middleware configuration
  - Credentials
- Allow configuration from **local files** (YAML, JSON) or environment variables.
- AI should default to **clear, explicit config patterns** to avoid guessing.

---

## ✅ Error Handling

Proxy must raise **meaningful, typed exceptions**:

✅ Examples:
~~~~
- ConnectionFailure
- RateLimitExceeded
- RetryExhausted
- EncryptionSignatureFailure
- InvalidConfiguration
~~~~

✅ Notes:
- Do not **swallow** critical errors.
- Business logic must be able to **catch** and respond.
- Rate limit exceedance should default to **blocking / delaying** if recoverable.
- Only **raise** if truly unrecoverable (e.g., quota hard failure).

---

## ✅ Extensibility

- Proxy must be **extensible**:
  - Add new middleware layers.
  - Swap transports.
  - Add new error types.
  - Extend tagging policies.

---

## ✅ Testing Requirements

- All implementations must be **pytest-asyncio testable**.
- Use **AsyncMock** to isolate transport.
- Provide **interface-level unit tests**.
- Support **integration tests** with real transports.

---

## ✅ Logging

- Support **structured logging**:
  - Include transport events.
  - Connection lifecycle.
  - Retry attempts.
  - Rate limit status.
- Allow **middleware-based logging** for easy extension.

---

## ❌ Anti-Patterns

- Exposing transport-specific details (e.g., HTTPX client) to business logic.
- Implementing retry or throttling inline instead of via plugins or middleware.
- Using bare `except:` to catch all exceptions without context.
- Tight coupling between proxy and transport implementation.

## 🛠 Logging and Observability

- Log proxy lifecycle events: `connect`, `disconnect`, `send`, `receive` with timestamps.
- Log error contexts including message tags, exception type, and retry count.
- Use structured logs for later analysis and tracing.

## 💡 Configuration Examples

```yaml
# proxy_config.yaml
transport: httpx
base_url: "https://api.example.com"
retry:
  retries: 3
  backoff_factor: 0.5
throttling:
  max_per_minute: 60
```

```python
from pydantic import BaseModel

class ProxyConfig(BaseModel):
    transport: str
    base_url: str
    retries: int = 3
    backoff_factor: float = 0.5
    max_per_minute: int = 60
```

---

## ✅ Summary

- **Async-first** design following AsyncCore rules.
- Pluggable, transport-agnostic interface.
- Optional tagging for rate limits and routing.
- Clean error handling with typed exceptions.
- Extensible via middleware.
- Fully testable and production-ready.


---

✅ Locked in as the BusinessProxy instructions.

If you'd like, just say ✅ Approve or 🛠️ Tweak! and we'll keep going.

# BusinessProxy Instructions for GitHub Copilot Chat

You are an AI assistant writing **a BusinessProxy abstraction layer** in Python for asynchronous systems.  

This document defines **the interface, responsibilities, and rules** for implementing a BusinessProxy that mediates between business logic and low-level transport details (e.g., HTTPX, FastAPI).  

It is intended for **clean, production-ready, testable code** with pluggable transport and error-handling strategies.

---

## ✅ Inherits Async Core

> ⚠️ Follow the [AsyncCore Instructions](async_core_instructions.md) for **all async correctness**, **I/O avoidance**, **TaskGroup management**, **cancellation handling**, and **test patterns**.  
>  
> This document does not repeat those rules but assumes full compliance.

---

## ✅ Purpose

- Encapsulate **transport details** (e.g., HTTPX, FastAPI).
- Expose a **clean async interface** to business logic:
  - `connect()`
  - `send()`
  - `receive()`
  - `close()`
- Hide retry, rate limit, encryption, and connection details behind the abstraction.

---

## ✅ Interface Shape

Your BusinessProxy must implement:

~~~~
class BusinessProxyProtocol:
    async def connect(self) -> None: ...
    async def send(self, message: Any, *, tags: Optional[List[str]] = None) -> None: ...
    async def receive(self) -> Any: ...
    async def close(self) -> None: ...
~~~~

✅ Notes:
- `tags` parameter supports optional **message tagging** for routing, rate limits, and priority.
- Implementations must remain **transport-agnostic** to business logic.

---

## ✅ Pluggable Transports

- Proxy must support **pluggable backends**:
  - e.g., HTTPX, FastAPI, WebSocket.
  - Plug-in approach must allow **easy swapping** without changing business logic.
- Use **dependency injection** or **factory patterns** for instantiation.

---

## ✅ Optional Plugins and Middleware

- Design for **middleware patterns**:
  - Rate limiting
  - Encryption/signature verification
  - Retry policies
  - Logging/auditing
- Middleware must be pluggable without modifying core proxy logic.

---

## ✅ Rate Limiting Support

- The proxy should **optionally** integrate rate limiting middleware.
- Support **multi-dimensional rate limits**:
  - Example: 100 calls/hour AND 5 calls/minute.
  - Enforce **all** dimensions (AND logic).
- Allow **tag-based** quotas:
  - Certain tagged messages count against certain quotas.
  - Others can be exempt or have separate limits.

---

## ✅ Retry Logic

- Provide **configurable retry strategies** for transient failures:
  - Exponential backoff.
  - Max retries.
  - Timeout ceilings.
- Retries should be **invisible** to business logic if successful.
- Expose **exhausted retries** as clear exceptions.

---

## ✅ Message Tagging

- `send()` and `receive()` must support **tags**:
  - Used for rate limiting.
  - Routing to appropriate middleware or queues.
  - Logging/auditing classifications.

✅ Examples:
~~~~
await proxy.send(message, tags=["priority:high", "service_call"])
~~~~

---

## ✅ Configuration

- Proxy should support **config injection**:
  - Project name
  - Transport selection
  - Middleware configuration
  - Credentials
- Allow configuration from **local files** (YAML, JSON) or environment variables.
- AI should default to **clear, explicit config patterns** to avoid guessing.

---

## ✅ Error Handling

Proxy must raise **meaningful, typed exceptions**:

✅ Examples:
~~~~
- ConnectionFailure
- RateLimitExceeded
- RetryExhausted
- EncryptionSignatureFailure
- InvalidConfiguration
~~~~

✅ Notes:
- Do not **swallow** critical errors.
- Business logic must be able to **catch** and respond.
- Rate limit exceedance should default to **blocking / delaying** if recoverable.
- Only **raise** if truly unrecoverable (e.g., quota hard failure).

---

## ✅ Extensibility

- Proxy must be **extensible**:
  - Add new middleware layers.
  - Swap transports.
  - Add new error types.
  - Extend tagging policies.

---

## ✅ Testing Requirements

- All implementations must be **pytest-asyncio testable**.
- Use **AsyncMock** to isolate transport.
- Provide **interface-level unit tests**.
- Support **integration tests** with real transports.

---

## ✅ Logging

- Support **structured logging**:
  - Include transport events.
  - Connection lifecycle.
  - Retry attempts.
  - Rate limit status.
- Allow **middleware-based logging** for easy extension.

---

## ❌ Anti-Patterns

- Exposing transport-specific details (e.g., HTTPX client) to business logic.
- Implementing retry or throttling inline instead of via plugins or middleware.
- Using bare `except:` to catch all exceptions without context.
- Tight coupling between proxy and transport implementation.

## 🛠 Logging and Observability

- Log proxy lifecycle events: `connect`, `disconnect`, `send`, `receive` with timestamps.
- Log error contexts including message tags, exception type, and retry count.
- Use structured logs for later analysis and tracing.

## 💡 Configuration Examples

```yaml
# proxy_config.yaml
transport: httpx
base_url: "https://api.example.com"
retry:
  retries: 3
  backoff_factor: 0.5
throttling:
  max_per_minute: 60
```

```python
from pydantic import BaseModel

class ProxyConfig(BaseModel):
    transport: str
    base_url: str
    retries: int = 3
    backoff_factor: float = 0.5
    max_per_minute: int = 60
```

---

## ✅ Summary

- **Async-first** design following AsyncCore rules.
- Pluggable, transport-agnostic interface.
- Optional tagging for rate limits and routing.
- Clean error handling with typed exceptions.
- Extensible via middleware.
- Fully testable and production-ready.


