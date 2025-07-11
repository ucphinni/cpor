# Business Proxy Plugin Architecture Instructions

This document defines the strict, 100%-accurate async plugin architecture for the Business Proxy layer.

It **inherits** from:

- `async_core.md` (for async lifecycle patterns, cancellation, etc.)  
- `business_proxy.md` (for connection management, error handling, and base proxy instructions)  

---

## Guards and Inheritance Notes

- **Do NOT duplicate** lifecycle or error handling instructions already defined in `async_core.md` or `business_proxy.md`.  
- Refer to those docs for basic async patterns and error policies.  
- This doc only specifies **plugin-specific interfaces and behaviors**.  
- AI must follow inheritance: assume all async lifecycle and error handling behaviors apply unless explicitly overridden here.  
- AI must NOT invent new lifecycle methods outside the documented plugin interface.  
- AI must ask for clarifications if plugin responsibilities or lifecycle are unclear.

---

## Plugin Interface Requirements

Plugins must conform exactly to this interface, supporting all lifecycle and messaging hooks asynchronously:

~~~~python
from typing import Protocol, Optional, Dict, Any

class BusinessProxyPlugin(Protocol):
    async def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Optionally configure the plugin with a config dict.
        Must be async, non-blocking.
        """
        ...

    async def start(self) -> None:
        """
        Called during business proxy connect phase.
        Must prepare any resources asynchronously.
        """
        ...

    async def stop(self) -> None:
        """
        Called during disconnect phase.
        Must clean up all resources asynchronously and support cancellation.
        """
        ...

    async def before_send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called before sending a message.
        Can modify and return the message.
        Must never block, always async.
        """
        ...

    async def after_receive(self, message: Dict[str, Any]) -> None:
        """
        Hook called after receiving a message.
        May process or store the message asynchronously.
        """
        ...
~~~~

---

## Plugin Registration and Lifecycle

- Business Proxy exposes:

  ~~~~python
  async def register_plugin(self, plugin: BusinessProxyPlugin) -> None:
      """
      Registers plugin and stores it internally.
      Plugins must be started/stopped in registration order.
      """
  ~~~~

- During `connect()`:
  - Business Proxy calls `await plugin.configure(config)` if config available  
  - Then calls `await plugin.start()` on all plugins, in order

- During `disconnect()`:
  - Business Proxy calls `await plugin.stop()` on all plugins, in registration order or reverse order (specify here which you prefer)

- Any exceptions in `configure()`, `start()`, or `stop()` must be:
  - Logged with full context  
  - Handled explicitly: either propagate to caller or continue with next plugin (define policy)

---

## Plugin Hooks Invocation

- On sending a message:

  ~~~~python
  async def send(self, message: Dict[str, Any]) -> None:
      for plugin in self.plugins:
          message = await plugin.before_send(message)
      # Proceed to send modified message
  ~~~~

- On receiving a message:

  ~~~~python
  async def _handle_received_message(self, message: Dict[str, Any]) -> None:
      for plugin in self.plugins:
          await plugin.after_receive(message)
      # Then dispatch message to business logic
  ~~~~

- Any exceptions during hook calls must be:
  - Logged with plugin identity and message content  
  - Handled according to explicit policy (continue, abort, retry)

---

## Error Handling Policy

- Plugins **must raise well-defined exceptions** on error.  
- Business Proxy catches plugin exceptions in lifecycle or hook calls.  
- Business Proxy logs all exceptions with detailed context.  
- Business Proxy **does not silently ignore** plugin exceptions unless explicitly configured to do so.  
- For unrecoverable errors during `start()`, `configure()`, or `stop()`, business proxy may abort operation or attempt fallback — **behavior must be explicitly defined** in the config or instructions.  
- Plugin errors in `before_send` or `after_receive` may abort the current send/receive or fallback to default behavior — **must be defined clearly**.

---

## Cancellation and Concurrency

- Plugins **must support cancellation via `asyncio.CancelledError`** during `stop()` or any long-running operation.  
- Business Proxy propagates cancellation signals to all plugins on shutdown.  
- All plugin async calls are awaited properly to ensure no task leaks.  
- Plugin lifecycle methods and hooks should not block or run long sync code.

---

## Configuration and Validation

- Plugins receive configuration either via `configure(config: dict)` or constructor params.  
- Plugin configuration schema validation is plugin’s responsibility.  
- Business Proxy ensures config is passed properly during registration/startup.  
- Plugins may request reconfiguration dynamically via `configure()` calls.

---

## Testing and Type Safety

- Plugins **must be unit testable** using async test frameworks (e.g., pytest-asyncio).  
- Full type annotations are required for all plugin interfaces and public methods.  
- Plugins must pass static analysis (mypy, ruff).  
- Plugins must include integration tests verifying lifecycle calls, hooks, error paths, and cancellation.

---

## Performance and Resource Management

- Plugins must avoid blocking or CPU-intensive synchronous code.  
- Plugins are responsible for managing their own resources (e.g., sockets, DB connections).  
- Plugins must properly cleanup to avoid memory or resource leaks on `stop()`.  
- Plugins must behave well under high concurrency, supporting multiple simultaneous sends/receives.

---

## AI Behavior Guardrails

- AI **must never invent plugin interface methods or lifecycle steps** not defined here.  
- AI **must ask clarifying questions** if input is ambiguous or incomplete.  
- AI **must not fill gaps silently** with guesses or assumptions.  
- AI must produce **100% valid async Python code**, respecting `await` usage strictly.  
- AI must generate explicit error handling and logging as specified.  
- AI should emit `TODO` comments if manual developer input is needed.

---

## Summary

This plugin architecture specification guarantees:

- Strict async lifecycle management  
- Explicit error handling and cancellation  
- Clear plugin hook semantics  
- Safe extensibility without AI guesswork  
- Maximum AI correctness and first-time code success  

