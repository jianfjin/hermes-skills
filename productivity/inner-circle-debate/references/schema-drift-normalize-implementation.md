# Schema Drift Normalization Pattern (2026-05-20 Council Resolution)

## Context

Mock data schemas for upstream WP services (WP2/WP3/WP8) will diverge from real consortium data. The council voted 5/5 to add a version-aware normalization layer NOW rather than waiting for M3 when real data arrives.

## Architecture

A single file (`pathfinder/adapters/upstream.py`) with:
1. Explicit field-mapping dicts keyed by schema version
2. Unknown version → ValueError (fail fast)
3. Unknown fields → logged warning + passthrough (don't crash)
4. Dijkstra's invariants: completeness, identity, surjectivity, no silent failure

```python
_WP3_NODE_NORMALIZERS = {
    "v1": {"node_id": "node_id", "label": "label", ...},
    "charite_v1": {"id": "node_id", "title": "label", "desc": "description", ...},
}

def _normalize_record(raw, mapping, version, label) -> dict:
    normalized = {}
    for raw_key, raw_value in raw.items():
        canonical = mapping.get(raw_key)
        if canonical:
            normalized[canonical] = raw_value
        else:
            logger.warning("Schema drift: unknown field %r", raw_key)
            normalized[raw_key] = raw_value
    # I1 check: missing canonical fields → warning
    return normalized
```

## Cost

€175-€580 (1 person-day). Prevents €500K M3 firefight when real data diverges.

## Key insight (雪峰)

"M3数据合同到了改YAML 10分钟。M3失败概率从70%降到10%以下。"

## Key insight (Musk)

"€2K decision prevents €500K M3 firefight. Do it this week."

## Related

Council debate record: docs/records/2026-05-20-council-debate-schema-drift.md
Implementation: feature/schema-normalize-layer (13 tests, all pass)
