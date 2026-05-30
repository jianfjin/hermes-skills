# View-Model → Self-Contained HTML Rendering Pattern

Pattern for rendering structured data as self-contained, zero-dependency HTML reports, developed during the SCAILED WP4 Pathfinder visualization build (2026-05-19).

## Architecture

```
Raw JSON/dict → Adapter (validation + mapping) → frozen @dataclass ViewModels → Renderer → HTML string
```

## Layers

### 1. Schemas (view model dataclasses)

All frozen (`frozen=True`). Templates receive dataclass instances, never raw dicts.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Summary:
    status: str
    confidence: float
    # ... fields

@dataclass(frozen=True)
class ReportViewModel:
    summary: Summary
    items: tuple[Item, ...] = ()
```

Rationale: Dicts are mutable, untyped, and allow silent key-typo bugs. Dataclasses fail fast. Frozen ensures templates can't mutate shared state.

### 2. Adapter (JSON → ViewModels)

Single entry point: `def build_view_model(raw: dict) -> ReportViewModel`. Handles:
- Shape validation (raise domain-specific error, not KeyError)
- Condition/field resolution (matching rule conditions against user answers)
- Back-references (e.g., blocker text → triggering rule)
- Edge cases: missing keys, None values, empty collections

Never pass `raw` dict directly to a template.

### 3. Renderer (ViewModels → HTML)

Pure Python string formatting. One function: `def render_html(vm: ReportViewModel) -> str`. Returns a complete `<!doctype html>...` document.

Template structure: Python triple-quoted string with `{placeholders}`. No Jinja2, no templating engine — string `.format()` is sufficient for frozen dataclass input.

CSS: inline `<style>` block in the template. Use CSS custom properties (`--ivory`, `--slate`, etc.) for theming. html-spec ivory theme or architecture-diagram dark theme.

Sections: use `{section_name}` placeholders, each populated by a dedicated `_render_*(vm)` function. This keeps the template readable and each section independently testable.

Interactive elements: `<details>/<summary>` for expand/collapse. Pure CSS `transform: scale()` for zoom. No JavaScript.

### 4. Delivery

FastAPI endpoint with query parameter: `GET /report?format=html` returns `HTMLResponse`. Default `?format=json` returns original JSON unchanged.

## Key Design Decisions (Council-Verified)

1. **One file, vertical scroll, no tabs** (Musk's rule). Separate views → separate HTML files was rejected as "admission the views shouldn't have been separate."

2. **No JS framework, no CDN** (Linus's rule). Pure HTML/CSS/SVG. Zoom/pan via CSS, expand/collapse via `<details>`, hover via `:hover`.

3. **Data contracts before rendering** (Guido's rule). schemas.py must be written and validated before any HTML. Three templates depending on magic dict keys is a time bomb.

4. **Subgraph, not full DAG** (Linus's rule). When rendering graphs, render only the path-relevant subgraph. "1000-node concerns are FUD — you're rendering subgraphs."

## Pitfalls

- **Don't over-estimate SVG layout**. Hand-writing a DAG layout engine for arbitrary graphs is a multi-day research task. Either use graphviz CLI (`dot -Tsvg`) and post-process in Python, or use a simple layered layout (maturity_level = x coordinate, stack nodes vertically within each level).

- **Test what the template produces, not what the code does**. Assert `"<svg" in html`, not `svg_parts is not None`. HTML correctness matters more than internal state.

- **`.get(key, default)` doesn't guard against explicit `None`**. If the dict has `{"key": None}`, `.get("key", [])` returns `None`, not `[]`. Use `.get("key") or []` instead.
