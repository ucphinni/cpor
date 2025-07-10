# Extensibility and Maintainability Vision for AI Code Generation

This document is a **guiding philosophy** for AI-assisted development in this repo. It’s not a step-by-step instruction set, but a *meta-layer* to check whether the AI’s solutions remain flexible, modular, and adaptable over time.

> Use this to ensure your generated code doesn’t become hard to extend or maintain.

---

## ✅ Core Principles

- **Explicit Interfaces**
  - Define clear, minimal contracts between layers.
  - Use protocols or ABCs if appropriate.
  - Don’t leak implementation details upward.

- **Separation of Concerns**
  - Business logic should not know or care *how* transport, storage, security are implemented.
  - Keep IO (network, disk) isolated from domain logic.

- **Pluggability**
  - Make it easy to swap implementations (e.g., HTTPx → AIOHTTP, SQLite → Postgres) without rewriting business code.
  - Favor dependency injection over hard-coded singletons.

- **Minimal, Composable Modules**
  - Prefer many small, focused modules over giant "god objects."
  - Aim for single responsibility per module or class.

- **Explicit Error Handling**
  - Raise meaningful exceptions.
  - Don’t swallow errors or guess at fixes.
  - Allow the caller to decide how to recover.

---

## ✅ Extension Strategy

When you need new functionality:

- **DO**
  - Add a new plugin or adapter rather than editing existing code.
  - Extend interfaces cleanly (subclass, protocol, strategy).
  - Write tests for the new extension.

- **DON’T**
  - Patch business logic to know about specific transports.
  - Add conditional logic all over the place for “if HTTPx then…”

---

## ✅ Guardrails for AI Code Generation

When using this vision with AI:

- Always ask:
  - “Will this design allow me to replace the implementation later?”
  - “Is this new dependency isolated from business logic?”
  - “Can I test this module in isolation?”

- Insist the AI:
  - Explain the separation of concerns in its design.
  - Document interfaces clearly.
  - Highlight any tight coupling or hidden assumptions.

---

## ✅ Example Red Flags to Catch

- Direct use of transport clients in business logic (e.g. `AsyncClient.get()` in core).
- Hard-coded config paths, URLs, secrets.
- Business classes with too many responsibilities.
- Mixed sync/async code without clear boundaries.
- Opaque error handling that hides root causes.

---

## ✅ Example Good Patterns

- A `TransportProxy` interface with a `send()` and `receive()`.
- Business logic taking an injected `TransportProxy`, unaware of HTTPx or FastAPI.
- Configuration passed at startup, not hard-coded.
- Context managers for resources.
- Modular plugins for encryption, rate limiting, retries.

---

## ✅ Fallback Strategy

When in doubt:
- Ask the human developer for clarification.
- Suggest questions the human might want to answer.
- Don’t make assumptions about use cases or infrastructure.
- Fail loudly rather than silently.