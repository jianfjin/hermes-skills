# Schema Drift Council Debate Pattern (2026-05-20)

## When to Use

When mock/test data schemas may diverge from real consortium/partner data schemas, and the fix radius is known to be small (one file), but the cost of waiting is high (demo failure at M3).

## Debate Composition

| Seat | Role | Focus Question |
|------|------|---------------|
| Guido (CLA) | API contracts | Where does normalization live? Dict-to-dict mapper or dataclass deserializer? |
| Linus (Arch) | Architecture | Where in the pipeline — adapter or service layer? Minimum change for all failure modes? |
| Dijkstra (CSO) | Formal correctness | Invariants: completeness, identity, surjectivity, no silent failure |
| Xuefeng (CSA) | Cost audit | Build now (€175) vs wait for M3 (€500K firefight)? |
| Musk (CVO) | First principles | Irreducible data contract between system and consortium |

## Council Verdict (5/5 Unanimous)

**Build now.** One file: `pathfinder/adapters/upstream.py`.
**Cost**: €175-€580 (1 person-day).
**Pattern**: `_NORMALIZERS: dict[version, callable]` + `normalize(raw, version) → canonical dict`.

## Key Quotes

- Xuefeng: "€175买保险。M3数据合同到了改YAML 10分钟。不做就是赌M3的数据跟mock一样——这种赌局十赌九输。"
- Musk: "€2K decision prevents €500K M3 firefight."
- Dijkstra: "A 20-line explicit mapping table with exhaustive else: raise beats a 200-line flexible reflection-based normalizer."
- Linus: "You identified failure modes. You have the file. You have a developer. Why the hell would you wait for the crisis?"

## Implementation Skeleton

```python
_NORMALIZERS = {
    "v1": {"field": "field"},  # identity passthrough
    "partner_v1": {"their_name": "our_name"},  # field rename
}

def _normalize_record(raw, mapping, version, label):
    normalized = {}
    for k, v in raw.items():
        canonical = mapping.get(k)
        if canonical:
            normalized[canonical] = v
        else:
            logger.warning("Schema drift [%s v%s]: unknown field %r", label, version, k)
            normalized[k] = v  # passthrough, don't drop
    return normalized

def _resolve_normalizer(normalizers, version, label):
    version = version or "v1"
    if version not in normalizers:
        raise UpstreamClientError(f"Unsupported {label} schema version: {version!r}")
    return normalizers[version]
```

## Dijkstra's 4 Invariants

1. **I1 (Completeness)**: normalize output must contain all fields downstream needs
2. **I2 (Identity)**: normalize(normalize(x)) = normalize(x) for canonical records
3. **I3 (Surjectivity)**: normalize codomain = domain model field Cartesian product
4. **I4 (No silent failure)**: input field not in mapping domain → alert (log warning)
