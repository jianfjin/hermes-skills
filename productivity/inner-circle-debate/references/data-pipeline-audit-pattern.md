# Data Pipeline Audit — Normalizer→Constructor Data Loss (2026-05-24)

## Bug Pattern

A field is added to the **schema** (validation layer), mapped in the **normalizer** (transformation layer), but **hardcoded to None in the constructor** (instantiation layer). The data is validated, transmitted, then silently discarded.

## Discovery Path

Both Linus (Arch) and Xiaolong (Eng) caught this independently during a 3-seat audit:

1. Schema added `effective_from` / `effective_until` as optional date fields
2. Normalizer (`_WP8_RULE_NORMALIZERS`) was updated to map them
3. But the `Rule(...)` constructor had `effective_from=None, effective_until=None` — hardcoded
4. The rule fixture had `"effective_from": "2026-06-01"` — data passed through normalizer, then discarded

## Root Cause

Multi-stage data pipelines where each stage is written at different times.

## Detection

- **Code review**: Trace every field from schema → normalizer → constructor.
- **Automated**: Test comparing schema field names against constructor params.

## Mitigation

```python
# Before: hardcoded None
effective_from=None,
effective_until=None,

# After: read from normalized data
effective_from=_parse_date(r.get("effective_from")),
effective_until=_parse_date(r.get("effective_until")),
```

With helper:

```python
def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
```

## Broader Pattern

Any pipeline: REST normalizer → model, fixture loader → dataclass, config parser → config.

**Invariant: every key the normalizer maps must be consumed by the constructor.**
