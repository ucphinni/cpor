
# Async File I/O Instructions for GitHub Copilot Chat

You are an AI assistant that writes **correct, idiomatic, and testable async file I/O code** in Python using **aiofiles**. These instructions assume [AsyncCore instructions](aipyasync-core.instructions.md) are in use for core async patterns, so testing, cancellation, and async correctness are inherited and not repeated here.

---

## ✅ Priority: Correct, Minimal, Testable Async File I/O

- Prioritize **correctness** and **testability**.
- Use **async/await** idioms consistently.
- Avoid blocking the event loop; **never use built-in `open()` in async code**.
- Use **aiofiles** exclusively for file operations.
- Always close files properly using `async with`.
- Use explicit file modes (`'r'`, `'rb'`, `'w'`, `'wb'`, etc.).
- Use **UTF-8 encoding** by default unless otherwise specified.
- Handle **random access** and **sequential** reads/writes as needed.
- Use **pathlib.Path** for path manipulation and normalize paths.
- Add **unit tests** with **pytest-asyncio** alongside code.
- Add **reasonable timeouts** if file operations could hang (rare but possible on networked filesystems).
- Start **asking questions** if usage patterns are unclear or ambiguous.

---

## ✅ Usage Patterns

- Use **async with aiofiles.open(path, mode, encoding='utf-8') as f** for file context management.
- For **sequential reading/writing**, read/write in chunks to avoid memory issues.
- For **random access**, use `await f.seek(offset)` before reading/writing.
- Always explicitly specify mode and encoding.
- Normalize paths with `Path(path).resolve()` before use.
- For binary files, use modes `'rb'` and `'wb'` without encoding.
- For text files, use modes `'r'` and `'w'` with UTF-8 encoding.

---

## ✅ Guardrails and Red Flags

> **❗️ Red Flag:** Never use built-in `open()` in async code — it blocks the event loop.  
> **❗️ Red Flag:** Always explicitly specify file mode and encoding.  
> **❗️ Red Flag:** Match data type to mode: text mode expects `str`, binary mode expects `bytes`.  
> **❗️ Red Flag:** Always check for file existence before reading using `aiofiles.ospath.exists()` or fallback to `Path.exists()`.  
> **✅ Guardrail:** Use `asyncio.Lock` or other coordination primitives to prevent concurrent write conflicts.  
> **✅ Guardrail:** Handle `PermissionError` explicitly to provide clear error messages.  
> **✅ Guardrail:** For critical writes, write to a temporary file first, then atomically rename to the target file.  
> **✅ Guardrail:** Normalize all paths with `Path.resolve()` to ensure cross-platform correctness.  
> **✅ Guardrail:** When uncertain about usage, **ask clarifying questions** before generating code.

---

## ✅ Example: Sequential Reading in Chunks

~~~~python
import aiofiles

async def read_file_in_chunks(path: str, chunk_size: int = 1024) -> str:
    contents = []
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            contents.append(chunk)
    return ''.join(contents)
~~~~

---

## ✅ Example: Random Access Write

~~~~python
import aiofiles

async def write_at_offset(path: str, data: str, offset: int) -> None:
    async with aiofiles.open(path, mode='r+', encoding='utf-8') as f:
        await f.seek(offset)
        await f.write(data)
        await f.flush()
~~~~

---

## ✅ Exception Handling Example

~~~~python
import aiofiles
import asyncio

async def safe_write(path: str, data: str) -> None:
    try:
        async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
            await f.write(data)
    except PermissionError as e:
        # Log or handle permission errors gracefully
        print(f"Permission denied for file {path}: {e}")
        raise
    except asyncio.CancelledError:
        # Cleanup if needed before task cancellation
        print("Write operation cancelled.")
        raise
~~~~

---

## ✅ Unit Testing Async File I/O

- Use **pytest-asyncio** to write async test functions.
- Use **tempfile.TemporaryDirectory** or **tempfile.NamedTemporaryFile** for isolated test files.
- Test **both sequential and random access** scenarios.
- Mock file operations with **AsyncMock** if needed.
- Ensure tests clean up temporary files to avoid pollution.

---

## ✅ Summary

- Use **aiofiles.open** exclusively in async code.
- Always specify **mode** and **encoding** explicitly.
- Normalize paths with **Path.resolve()**.
- Read and write files **in chunks** for large files.
- Use **asyncio.Lock** to prevent concurrent write issues.
- Always **check file existence** before reading.
- Handle **PermissionError** and **CancelledError** explicitly.
- Use **temp file + rename** for critical writes.
- Write **pytest-asyncio** unit tests with coverage for edge cases.
- If usage patterns are unclear, **ask questions** before generating code.

---

< ! Important AI Guardrail:  
**Do not modify these instructions unless reviewing for accuracy.**  
These guardrails ensure AI produces idiomatic, safe, and testable async file I/O code.  
Always adhere strictly to the async file I/O best practices specified here.  
>

