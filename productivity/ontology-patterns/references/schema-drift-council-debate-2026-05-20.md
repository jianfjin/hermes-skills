# Schema Drift Mitigation — Council Debate Reference

**Date**: 2026-05-20
**Council**: 5 seats (Guido/Linus/Dijkstra/Musk/Xuefeng)
**Verdict**: 5/5 — Build normalize layer NOW, not at M3

## Consensus Architecture

The council rejected both "wait for M3" (70%+ crash probability) and "full normalize architecture" (premature for unseen schemas). The middle path:

1. **Python dict normalizers** (not YAML config — simpler for ≤3 schema versions)
2. **Version-aware dispatch**: `_resolve_normalizer(normalizers, version, label)`
3. **Exhaustive mapping**: unknown field → WARNING log, not KeyError
4. **Unknown version → ValueError at startup** (fail fast)
5. **Cardinality not a concern**: adapter doesn't care about record count

## Implementation (scailed_wp4, feature/schema-normalize-layer)

```python
# pathfinder/adapters/upstream.py
_WP3_NODE_NORMALIZERS = {
    "v1": {"node_id": "node_id", "label": "label", ...},  # passthrough
    "epidata_v1": {"id": "node_id", "title": "label", "level": "maturity_level", ...},
}

def _normalize_record(raw, mapping, version, label) -> dict:
    # Dijkstra I4: unknown fields logged, not silently dropped
    for raw_key, raw_value in raw.items():
        canonical = mapping.get(raw_key)
        if canonical is not None:
            normalized[canonical] = raw_value
        else:
            logger.warning("Schema drift: unknown field %r", raw_key)
            normalized[raw_key] = raw_value
    return normalized
```

## Key Numbers
- Fix radius: 1 file (`upstream.py`)
- Implementation: 0.3 person-days (€175)
- Tests: 13 (version dispatch, field rename, unknown field warning, integration)
- M3 transition cost: edit mapping dict, 10 minutes

## Quotable Quotes
- Musk: "€2K decision prevents €500K M3 firefight"
- Xuefeng: "现在花0.3人天把M3失败概率从70%降到10%以下"
- Dijkstra: "A 20-line explicit mapping table beats a 200-line flexible reflection-based normalizer"
- Linus: "One file, one normalize function, one validation gate. Do it now."
- Guido: "Simple is better than complex. The mapping table is almost embarrassingly simple."
