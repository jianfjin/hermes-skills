# Data-to-HTML Pipeline with View Model Contract Layer

Pattern extracted from 2026-05-19 Pathfinder report visualization build.

## The Pattern

```
API JSON (dict) → adapter.py → frozen @dataclass → renderer.py → self-contained HTML
                     │                                    │
                     │ validates shape                    │ never touches raw dict
                     │ resolves condition matches         │ only reads typed fields
                     │ maps blockers back to rules        │
```

## Guido's Rule

Templates receive **frozen dataclasses**, never raw `dict[str, Any]`. Dicts are mutable, key-missable time bombs. Frozen dataclasses are honest — the type system catches schema drift at import time.

## File Structure

```
pathfinder/visualization/
  __init__.py
  schemas.py    — @dataclass(frozen=True) view models
  adapter.py    — raw JSON → validated view models
  renderer.py   — view models → self-contained HTML string
```

## Schema Design

```python
@dataclass(frozen=True)
class ReadinessSummary:
    status: str           # "blocked" | "ready"
    confidence: float     # 0.0-1.0
    path_backend: str     # "python" | "cypher"
    audit_chain_valid: bool

@dataclass(frozen=True)
class ReportViewModel:
    summary: ReadinessSummary
    blockers: tuple[BlockerEvidence, ...]
    path_steps: tuple[PathStepView, ...]
    triggered_rules: tuple[RuleCard, ...]
```

## Adapter Responsibilities

1. Validate input shape (raise domain-specific error, not KeyError)
2. Map JSON fields to typed dataclass fields
3. Resolve cross-references (e.g., blocker text → triggering rule)
4. Compute derived fields (status colors, labels, display strings)

## Renderer Constraints (Musk's Rule)

- One HTML file. Vertical scroll. No tabs. No JavaScript.
- html-spec ivory theme (--ivory, --slate, --clay CSS variables)
- 4 sections: Readiness → Blockers → Path → Evidence
- Machine-readable trace block at bottom
- Zero external dependencies

## FastAPI Integration

```python
@app.get("/v1/assessments/{id}/report")
def report(format: str = Query(default="json")):
    raw = service.report(id)
    if format == "html":
        vm = build_view_model(raw)
        html = render_html(vm)
        return HTMLResponse(content=html)
    return raw
```

One endpoint, one query param. JSON is the single source of truth; HTML is a deterministic rendering.
