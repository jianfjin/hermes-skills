# JSON → View Model → HTML Pattern (Guido's Contract Layer)

When generating HTML from an existing JSON API output (reports, dashboards, data views):

## The stack

```
API JSON dict → adapter.py (validates + transforms) → frozen @dataclass → renderer.py (HTML)
```

Templates never see raw dicts. Every layer has a contract.

## Step 1: View model dataclasses (schemas.py)

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # immutability: template can't mutate
class ReportViewModel:
    summary: ReadinessSummary
    items: tuple[ItemView, ...]
    metadata: dict  # machine-readable trace

@dataclass(frozen=True)
class ItemView:
    label: str
    status: str  # enum-like: "completed" | "blocked" | "pending"
    
    def status_color(self) -> str:  # view logic lives HERE, not in template
        return {"completed": "#166534", "blocked": "#9B2C2C"}.get(self.status, "#000")
```

Rules:
- `frozen=True` always — prevents template mutation bugs
- View logic (colors, labels, formatting) lives as methods on the dataclass
- Use `tuple` for collections — immutable
- Include `generated_at: str` for audit trail

## Step 2: Adapter (adapter.py)

```python
class AdapterError(ValueError):
    """Raised when input JSON doesn't match expected shape."""

def build_view_model(raw: dict) -> ReportViewModel:
    _validate_shape(raw)  # fail fast with clear message
    # ... extract, transform, build dataclasses ...
    return ReportViewModel(...)
```

Rules:
- Validate input shape BEFORE extraction — `KeyError` from missing keys is unhelpful
- `.get(key) or []` for nullable lists (`.get(key, [])` doesn't guard against explicit None)
- Match related entities back (e.g., blocker text → triggering rule)
- Handle empty collections gracefully — empty tuples, not None

## Step 3: Renderer (renderer.py)

```python
def render_html(vm: ReportViewModel) -> str:
    """Pure function: view model → complete HTML string."""
    return TEMPLATE.format(
        section_a=_render_section_a(vm.items),
        section_b=_render_section_b(vm.summary),
    )
```

Rules:
- One function, one return — `str`
- Section renderers are private functions, each returns HTML fragment
- Use Python string `.format()` for template substitution (no Jinja2 dep)
- html-spec ivory theme CSS inline in the template string
- Zero JavaScript. Interactions via `<details>/<summary>` + CSS `:hover`
- Include machine-readable trace (JSON comment block) at page bottom

## Pitfalls

- **`.get(key, [])` fails on explicit None**. When JSON has `"key": null`, `.get(key, [])` returns `None` (not `[]`). Use `.get(key) or []`.
- **Don't pre-validate in the renderer**. If `vm.items` is empty, render a "no items" message — don't re-validate.
- **One HTML file, not three+tabs**. Musk's rule: tabs hide information. Vertical scroll with section headers.
- **Zero JavaScript**. `<details>` is native HTML. `:hover` is CSS. No onclick handlers.
