---
name: ontology-patterns
description: Ontology-driven architecture patterns for DataWego projects — Action Writeback, type-safe codegen from schema definitions, polymorphic interfaces, and FDE-style client embedding. Distilled from Palantir Ontology concepts, adapted for small-team scale without platform lock-in.
version: 1.0.0
category: productivity
---

# Ontology Patterns for DataWego

Applied ontology concepts for data-driven projects. Not Palantir — our own lightweight patterns.

## Trigger Conditions

- Designing a system that maps domain entities to a navigable graph
- Need to close the feedback loop on recommendations or decisions
- Evaluating whether to auto-generate types/models from a schema definition
- Planning client-embedded engineering or domain-expert translation roles
- User mentions "ontology", "Palantir", "semantic layer", or "digital twin"

## Core Patterns

### Pattern 1: Action Writeback (The Feedback Loop)

**Problem**: System emits recommendations but never learns whether they were followed.

**Solution**: Give every recommendation a lifecycle state machine.

```
Recommendation states:
  pending → accepted → in_progress → completed → verified
           ↘ rejected  → reason_captured
           ↘ ignored   → (timeout → flagged)

Database: recommendation_status ENUM + status_changed_at TIMESTAMPTZ + status_changed_by
Each state transition is an auditable event (append-only log).
```

**When to use**: Any system where users receive action items and the system should adapt based on whether they follow them. Regulatory compliance, project management, clinical decision support.

**Implementation**: Add a `recommendation_statuses` table with guarded transitions:

```python
# core/actions.py
class ActionState(Enum):
    ISSUED = "issued"; ACCEPTED = "accepted"; SKIPPED = "skipped"
    DEFERRED = "deferred"; IN_PROGRESS = "in_progress"
    COMPLETED = "completed"; BLOCKED = "blocked"

# Dijkstra requirement: deterministic guarded transitions
TRANSITIONS = {
    ActionState.ISSUED: {ActionState.ACCEPTED, ActionState.SKIPPED, ActionState.DEFERRED},
    ActionState.ACCEPTED: {ActionState.IN_PROGRESS, ActionState.SKIPPED, ActionState.DEFERRED},
    ActionState.IN_PROGRESS: {ActionState.COMPLETED, ActionState.BLOCKED},
    ActionState.COMPLETED: set(),   # terminal state
    ActionState.BLOCKED: {ActionState.IN_PROGRESS, ActionState.SKIPPED},
}
```

SQL:
```sql
CREATE TABLE action_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES assessment_sessions(id),
    recommendation_id UUID NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('issued','accepted','skipped','deferred','in_progress','completed','blocked')),
    reason TEXT, changed_by TEXT, changed_at TIMESTAMPTZ DEFAULT now(),
    previous_state TEXT, metadata JSONB
);
-- TRIGGER-based immutability (Linus audit fix, not RULE)

### Pattern 2: Schema-to-Codegen (Single Source of Truth)

**Problem**: Schema definitions (YAML/JSON) and code models (Pydantic/SQLAlchemy) drift apart. Hand-sync causes bugs.

**Solution**: Generate type-safe models from a single schema definition. Keep it simple.

```python
# 200-line script: yaml_to_pydantic.py
# Reads rules/*.yaml → emits core/generated_models.py

# Input (YAML):
#   object_types:
#     Stakeholder:
#       properties:
#         maturity_level: {type: integer, min: 1, max: 5}
#         compliance_status: {type: string, enum: [compliant, partial, non_compliant]}

# Output (Pydantic):
#   class Stakeholder(BaseModel):
#       maturity_level: int = Field(ge=1, le=5)
#       compliance_status: Literal["compliant", "partial", "non_compliant"]
```

**Requirements for generated code** (per Guido):
- Human-friendly field names (not auto-converted camelCase)
- Docstrings pulled from YAML descriptions
- Discriminated unions over Optional[Union[...]] soup
- Regenerated in pre-commit hook; never hand-edited
- CI validates: YAML → regenerate → git diff must be clean

**When NOT to use**: If you have fewer than 10 entity types. Hand-writing is cheaper.

### Pattern 3: Polymorphic Interfaces (Stakeholder Diversity)

**Problem**: Different stakeholder types (pharma, SME, academia) share common behaviors but differ in specifics.

**Solution**: Python Protocol classes — structural subtyping without inheritance.

```python
from typing import Protocol

class ComplianceSubject(Protocol):
    maturity_level: int
    compliance_status: str
    def applicable_regulations(self) -> list[str]: ...

class PharmaCompany:
    maturity_level: int = 2
    compliance_status: str = "partial"
    def applicable_regulations(self) -> list[str]:
        return ["GDPR-Art.37", "EHDS-Art.50", "MDR-Annex-I"]

class AcademicLab:
    maturity_level: int = 4
    compliance_status: str = "compliant"
    def applicable_regulations(self) -> list[str]:
        return ["GDPR-Art.89", "EHDS-Art.46"]
```

Any object that satisfies `ComplianceSubject` can be passed to the compliance checker. No class hierarchy needed.

### Pattern 4: FDE Lite (Client-Embedded Engineering Without Perpetual On-Site)

**Problem**: Domain expertise lives with the client (Epidata's QA team, CHARITE's regulatory experts). Engineers can't model what they don't understand. Full Palantir FDE (permanent embedded) is too expensive.

**Solution**: Hybrid model — technical lead does on-site workshops, domain translation happens through structured artifacts.

```
Phase 0 (M1-M2): 1-2 on-site workshops led by CTO/tech lead
  → Output: domain glossary, entity-relationship sketches, sample data

Phase 1+ (M4+): Remote bi-weekly sync with domain expert
  → Artifacts: YAML rule files reviewed by domain expert (not code)
  → Rule files are the translation layer — domain experts can read YAML

Scaling: if client count > 2, hire Technical Business Analyst
  → Profile: compliance consultant bored at Big 4, can write Python
  → NOT a pure engineer, NOT a pure consultant — hybrid
```

**Decision tree for FDE needs**:

```
Single client, pre-revenue → Tech lead does workshops. No FDE hire.
2-3 clients, pre-revenue → Tech lead + 1 part-time domain translator.
3+ clients, revenue → Hire dedicated Technical Business Analyst.
Enterprise scale → Consider full FDE embed (but this is Palantir money).
```

### Pattern 5: Schema Migration Layer (Mock→Real Data Transition)

**Problem**: Mock data uses specific field names. When real consortium data arrives (WP2 from CHARITE, WP3 from Epidata), field names will differ. The adapter hardcodes mock field names (`n["node_id"]`), causing KeyError on first contact with real data.

**Council consensus** (2026-05-20, 5 seats: Guido/Linus/Dijkstra/Musk/Xuefeng): Build a **version-aware normalize layer** in the adapter, not a full architecture.

**Cost**: 0.3 person-days (€175). **Timing**: Now (during mock data phase), before M3 data contracts arrive. Xuefeng's risk model: waiting = 70%+ probability of M3 demo crash.

**Solution**: Python dict-based normalizers with explicit, exhaustive field-name mappings:

```python
# pathfinder/adapters/upstream.py — single file change
_WP3_NODE_NORMALIZERS = {
    "v1": {"node_id": "node_id", "label": "label", ...},         # identity passthrough
    "epidata_v1": {"id": "node_id", "title": "label",            # real schema
                    "level": "maturity_level", "applicable_to": "stakeholder_types"},
}

def _normalize_record(raw: dict, mapping: dict, version: str, label: str) -> dict:
    """Translate raw field names to canonical names. Dijkstra I4: unknown fields logged."""
    normalized = {}
    for raw_key, raw_value in raw.items():
        canonical = mapping.get(raw_key)
        if canonical is not None:
            normalized[canonical] = raw_value
        else:
            logger.warning("Schema drift [%s v%s]: unknown field %r", label, version, raw_key)
            normalized[raw_key] = raw_value
    return normalized

def _resolve_normalizer(normalizers, version, label):
    """Version dispatch. Unknown version → ValueError at startup (fail fast)."""
    version = version or "v1"
    if version not in normalizers:
        raise UpstreamClientError(f"Unsupported schema version: {version!r}")
    return normalizers[version]
```

**Key design rules** (per Guido + Dijkstra):
- Mapping table is **explicit and exhaustive** — no fuzzy matching, no guesswork
- Unknown fields → WARNING log, value kept as-is (don't silently drop)
- Unknown version → ValueError at startup (fail fast)
- Cardinality not a concern — adapter doesn't care about record count (Musk)
- M3 transition: add new version dict entry, 10 minutes

**Failure matrix coverage**:

| Schema Change | Handled By |
|--------------|------------|
| Field rename | Normalize mapping |
| New field added | Passthrough (mapping.get returns None → kept as-is) |
| Field removed | I1 check: "missing canonical fields" WARNING |
| Type change | `import_wp*` validation gate (separate layer) |
| Nested structure change | Recursive normalize call per substructure |

**When NOT to use**:
- If you already have the real schema → code directly to real fields
- If you have >5 schema versions → switch to versioned dataclass deserializers
- If the data comes from a versioned OpenAPI spec → use the spec as source of truth

**Reference**: `references/schema-drift-council-debate-2026-05-20.md` — full council debate record, implementation details, test coverage.

## When NOT to Apply These Patterns

- **Don't ontology-wash a CRUD app**: If your system has 3 entities and no graph, YAGNI.
- **Don't codegen for <10 types**: Hand-writing is cheaper and the script maintenance cost exceeds the benefit.
- **Don't call it "ontology" to clients**: Call it "type system" or "data model." (Per Linus: "Call it a schema. Your users will thank you.")
- **Don't build a marketplace**: You have one regulatory framework. Build it once. Marketplace is M30+ territory.

## Relationship to Other Skills

- `inner-circle-debate`: Use the External Eval debate mode (Musk + Dijkstra + Guido + Linus + Xuefeng) when evaluating third-party frameworks or patterns for adoption.
- `html-spec`: Use Action Writeback state machines in architecture specs.
- `html-plan`: FDE workshop scheduling goes in implementation plans.

## References

- Council debate 2026-05-15: 7-seat vote on Palantir Ontology adoption. Verdict: adopt 20% (action writeback, codegen, polymorphism), reject full platform model. No FDE hire yet. Full debate in `scailed_wp4/council_debate_20260513/`.
- Palantir Ontology docs: https://www.palantir.com/docs/foundry/ontology/overview/ (proprietary — concepts only, no code dependency)
