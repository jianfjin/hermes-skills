# Background Event Loop — Bridging Sync and Async Python Code

A common anti-pattern: creating a new event loop per call via
`asyncio.new_event_loop()` + `loop.run_until_complete()`. This fails at
runtime with `RuntimeError: Cannot run the event loop while another loop
is running` when called from certain async contexts, and leaks event
loop resources under load.

## The Pattern: Single Daemon-Thread Background Loop

Maintain one background event loop in a daemon thread. Push coroutines
to it via `asyncio.run_coroutine_threadsafe()` and block the caller with
`future.result(timeout=...)`.

```python
# bg_loop.py
from __future__ import annotations

import asyncio
import threading
from typing import Any

_loop: asyncio.AbstractEventLoop | None = None
_lock = threading.Lock()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        with _lock:
            if _loop is None or _loop.is_closed():
                _loop = asyncio.new_event_loop()
                t = threading.Thread(
                    target=_loop.run_forever,
                    daemon=True,
                    name="bg-loop",
                )
                t.start()
    return _loop


def run_async(coro: Any, timeout: float = 5.0) -> Any:
    """Schedule a coroutine on the background loop and wait for result.

    Safe to call from any thread. No new event loop is created.
    """
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)
```

## Usage

```python
from bg_loop import run_async

# From any sync context (e.g. FastAPI endpoint, synchronous service):
result = run_async(some_async_function(arg1, arg2), timeout=2.0)
```

## When to Use

- Sync service code that needs to call async database drivers (e.g.
  syncc`__init__` calling asyncpg)
- Fire-and-forget background writes (best-effort, non-blocking)
- Calling into async libraries from synchronous test code

## When NOT to Use

- Inside async endpoints or async middleware (just `await` directly)
- For latency-critical paths (the thread switch adds ~0.1ms overhead)
- When the coroutine produces a side-effect that must be synchronous
  with the caller's transaction (use a proper async stack instead)

## Pitfalls

- **Timeout**: Always set a timeout. A stuck coroutine blocks the
  caller's thread indefinitely.
- **Thread safety**: The coroutine runs on a different thread. Any
  shared state it accesses needs synchronization (lock, queue, etc.).
- **Cleanup**: The daemon thread exits when the process exits. If you
  need graceful shutdown, call `loop.call_soon_threadsafe(loop.stop)`.
- **Connection pooling**: If the background coroutine acquires
  connections from a pool (e.g. asyncpg), the pool must be
  thread-safe (most asyncpg pools are).
