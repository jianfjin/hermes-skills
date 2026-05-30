# SQLite Thread Safety Patterns for Hermes Event Bus

## Problem

The EventBusWriter singleton runs in a multi-threaded context (5-agent parallel writes, WAL checkpoint daemon thread, concurrent readers). SQLite's C-level WAL mode serializes file writes, but the Python `sqlite3.Connection` object is NOT thread-safe — concurrent operations from multiple threads produce `ProgrammingError`, `cannot commit - no transaction`, and `cannot start a transaction within a transaction`.

## Patterns

### 1. `check_same_thread=False`

Required on the `sqlite3.connect()` call when the connection will be accessed from any thread other than the creating thread.

```python
self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
```

Without this, ANY cross-thread access raises:
```
ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
```

### 2. Write Lock on the Writer Singleton

Even with `check_same_thread=False`, concurrent `execute()`/`commit()` calls on the same connection race at the Python level. Protect with a `threading.Lock`:

```python
class EventBusWriter:
    write_lock = threading.Lock()  # class-level, shared across all references

# In publish_event():
with writer.write_lock:
    conn.execute(...)
    conn.commit()
```

Without this, errors include:
- `cannot commit - no transaction is active` (another thread committed the implicit transaction)
- `cannot start a transaction within a transaction`
- `DatabaseError: no more rows available` (cursor consumed by another thread)

### 3. `row_factory = sqlite3.Row`

Required on the writer connection if any code reads back rows with dict-style access (`row["column_name"]`). Without it, rows are plain tuples and `row["col"]` raises `TypeError: tuple indices must be integers, not str`.

```python
self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
self._conn.row_factory = sqlite3.Row
```

### 4. Single-statement `execute()` vs Multi-statement `executescript()`

`conn.execute(sql, params)` only handles ONE SQL statement at a time. For multi-statement SQL (e.g., INSERT + UPDATE in one string), use `conn.executescript(sql)` — but `executescript()` does NOT support parameter binding (`?` placeholders).

**Wrong** — `execute()` with multi-statement SQL:
```python
SQL = "INSERT INTO ... ; UPDATE ... ;"
conn.execute(SQL, params)  # raises "You can only execute one statement at a time"
```

**Right** — separate calls:
```python
conn.execute("INSERT INTO ... WHERE id=?", (id_val,))
conn.execute("UPDATE ... WHERE id=?", (id_val,))
conn.commit()
```

### 5. Resetting Singletons Between Tests

Integration tests that create/delete the same database file between runs must reset both writer and reader singletons:

```python
# Teardown:
EventBusWriter._instance = None  # reset writer singleton
import subscribe_events as se
se._reader = None  # reset reader singleton
```

Without resetting the reader, an old connection from a previous test run continues to point to the deleted-then-recreated database file's inode, returning stale data (or nothing for a fresh DB).

### 6. Metric Ring Buffer Thread Safety

The `EventBusMetrics` dataclass accumulates data from multiple threads (publish, subscribe, checkpoint). The ring-buffer trim (`self.write_latencies = self.write_latencies[-N:]`) is a read-modify-write that races under concurrent calls.

```python
_lock: Lock = field(default_factory=Lock, repr=False)

def record_write(self, latency_ms: float) -> None:
    with self._lock:
        self.events_written += 1
        self.write_latencies.append(latency_ms)
```
