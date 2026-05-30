# Pathfinder Rule DSL — Reference Schema

This is a condensed reference to the Pathfinder V1 rule engine DSL, which
motivated the schema-driven validation pattern.  The full schema lives at
`pathfinder/core/rules/schema.json` in the scailed_wp4 project.

## Top-Level Bundle

```json
{
  "version": "gen-1000-rules-v1",
  "rules": [...],
  "tests": [...]
}
```

## Rule Object

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `rule_id` | yes | string | Pattern: `^[A-Z0-9_-]+$` |
| `rule_type` | yes | enum | `eligibility`, `exclusion`, `preference`, `override` |
| `priority` | yes | int 0-1000 | Higher = evaluated first |
| `applies_to` | yes | [string] | Stakeholder types; `["all"]` for universal |
| `condition` | yes | object | See condition DSL below |
| `action` | yes | object | See action structure below |
| `compliance_refs` | yes | [string] | Regulation refs like `GDPR-Art.9` |
| `source_doc_ref` | no | string | Default: `"demo-data"` |
| `rule_version` | no | string | Default: `"demo-rules-v1"` |
| `effective_from` | no | date\|null | Null = always |
| `effective_until` | no | date\|null | Null = never |
| `parent_rule_id` | no | string\|null | For versioning/overrides |

## Condition DSL (oneOf)

### Atomic condition

```json
{ "field": "answers.governance_maturity", "operator": "gte", "value": 4 }
```

### Compound AND

```json
{ "and": [ { "field": "answers.governance_maturity", "operator": "gte", "value": 4 }, { "field": "answers.compliance_maturity", "operator": "gte", "value": 3 } ] }
```

### Compound OR

```json
{ "or": [ { "field": "capabilities", "operator": "contains", "value": "data-catalog" }, { "field": "capabilities", "operator": "contains", "value": "audit-log" } ] }
```

### Compound NOT

```json
{ "not": { "field": "capabilities", "operator": "contains", "value": "legal-basis" } }
```

### Empty (always true)

```json
{}
```

### Operators

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `exists`

### Accessible Fields

- `answers.<question_id>` — questionnaire answers
- `maturity.<dimension>` — maturity scores by dimension
- `stakeholder_type`, `target_scenario` — bare fields
- `capabilities`, `missing_capabilities`, `regulatory_flags` — list fields

## Action Structure

```json
{
  "title": "Advanced readiness confirmed",
  "text": "Governance >= 4, compliance >= 3, and data-catalog or audit-log present.",
  "node_id": "readiness-report",
  "warning": "cross-border use case requires Adequacy Decision",
  "block": false
}
```

Only `title` and `text` are required. `node_id` and `warning` are nullable.
`block: true` produces a blocker in the path result.

## Compound Condition Nesting (Example from curated rule)

```json
{
  "and": [
    { "field": "answers.data_maturity", "operator": "gte", "value": 3 },
    {
      "not": {
        "and": [
          { "field": "capabilities", "operator": "contains", "value": "data-quality-kpi" },
          { "field": "capabilities", "operator": "contains", "value": "audit-log" }
        ]
      }
    }
  ]
}
```
