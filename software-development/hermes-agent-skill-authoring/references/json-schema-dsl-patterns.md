# JSON Schema Patterns for DSL Validation

Two proven patterns extracted from a real-world rules-engine formalisation. Both are reusable across any project that needs to validate structured DSLs (conditions, workflows, policies, queries).

---

## Pattern 1: Discriminated Union via `oneOf` + `$ref`

Use when a field can be one of several structurally different variants.

### Problem

A `condition` field used to be `"type": "object"` — a validation no-op. In practice it could be a compound expression (`{"and": [...]}`), an atomic comparison (`{"field": "x", "operator": "gte", "value": 3}`), or an empty always-true. These have completely different shapes.

### Solution

Define each variant as a `$def` subschema, then combine with `oneOf`:

```json
{
  "condition": {
    "oneOf": [
      { "$ref": "#/$defs/conditionAnd" },
      { "$ref": "#/$defs/conditionOr" },
      { "$ref": "#/$defs/conditionNot" },
      { "$ref": "#/$defs/conditionAtomic" },
      { "$ref": "#/$defs/conditionEmpty" }
    ]
  },
  "$defs": {
    "conditionAnd": {
      "type": "object",
      "required": ["and"],
      "properties": {
        "and": {
          "type": "array",
          "items": { "$ref": "#/$defs/condition" },
          "minItems": 1
        }
      },
      "additionalProperties": false
    },
    "conditionAtomic": {
      "type": "object",
      "required": ["field", "operator", "value"],
      "properties": {
        "field": { "type": "string", "pattern": "^(answers\\.|maturity\\.)?[a-zA-Z_][a-zA-Z0-9_]*$" },
        "operator": { "type": "string", "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "exists"] },
        "value": { "description": "Expected value. Type depends on the operator." }
      },
      "additionalProperties": false
    },
    "conditionEmpty": {
      "type": "object",
      "maxProperties": 0
    }
  }
}
```

### Key Design Decisions

1. **`additionalProperties: false`** on each variant — prevents typos like `"opreator"` from passing silently.
2. **Recursive `$ref`** — `conditionAnd.items` references `#/$defs/condition` (the parent `oneOf`), enabling arbitrarily nested `and`/`or`/`not`.
3. **`minItems: 1`** on arrays — a compound `{"and": []}` is meaningless.
4. **`maxProperties: 0`** on the empty variant — accepts `{}` but rejects `{"extra": true}`.
5. **No default overlap checker** — JSON Schema `oneOf` naturally ensures mutual exclusivity. Add `additionalProperties: false` and `required` to disambiguate.

### Pitfalls

- **`oneOf` validation errors are long** — jsonschema produces a single error for each variant that failed. For deep nesting, the error message can be thousands of lines. Catch `jsonschema.ValidationError` and extract the shortest `message` + the `absolute_path` for a human-readable error.
- **Field name pattern** — use a `pattern` constraint on field names to prevent injection of arbitrary state keys. Keep it permissive enough for future fields.
- **Empty vs missing** — `{}` (always true) is different from no condition at all. Make the distinction explicit in your schema: the former is a valid condition, the latter is not (use `required` at the parent level).

---

## Pattern 2: Migration from Hand-Written Validation to jsonschema

Use when you have a JSON Schema file that documents the data format, but the actual validation is done by hand-written Python checks that duplicate (and often drift from) the schema.

### Migration Steps

1. **Load the schema at module level** — `json.loads(Path("schema.json").read_text())`
2. **Replace hand-written field checks** with `jsonschema.validate(instance=bundle, schema=schema)`.
3. **Keep only semantic checks** that JSON Schema cannot express:
   - Duplicate IDs across the array
   - Cross-field conflict detection (e.g., same `(type, applies_to, condition)` tuple producing different actions)
   - Business-rule invariants (e.g., "exclusion rules must have block: true")
4. **Create a clear architecture**: the schema is the structural source of truth; the Python code handles only logic that requires programmatic reasoning.

### Result

```python
def validate_rule_bundle(bundle):
    # 1. Structural — dj.waveterminal catches everything: field shapes,
    #    required properties, enum values, pattern constraints, nullable types.
    jsonschema.validate(instance=bundle, schema=SCHEMA)

    # 2. Semantic — only what JSON Schema can't express.
    seen_ids = set()
    for rule in bundle["rules"]:
        if rule["rule_id"] in seen_ids:
            raise RuleValidationError(f"duplicate rule_id: {rule['rule_id']}")
        seen_ids.add(rule["rule_id"])
```

### Pitfalls

- **nullable fields** — JSON Schema requires explicit `"type": ["string", "null"]` for nullable fields. `"default": null` in the schema is documentation only; validation still rejects `null` if the type is `"string"`.
- **date `format`** — `"format": "date"` validates pattern but not semantics. `"2026-13-01"` passes format validation in most draft-07 implementations (it only checks the regex). Draft 2020-12 with `"format": "date"` and content-encoding can be stricter, but not all validators support it.
- **Hidden defaults** — `"default": "demo-rules-v1"` in JSON Schema is metadata; jsonschema does NOT inject defaults into the instance. If your code depends on default values, handle them in the Python model constructor, not in the schema.

---

## When to Use These Patterns

- Any project with a JSON/YAML configuration or rule format that has multiple structural variants
- Any project migrating from ad-hoc validation to schema-driven validation
- Projects where the schema and validator need to stay in sync and drift would cause silent data corruption
