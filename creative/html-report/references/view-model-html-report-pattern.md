# View Model → HTML Report Pattern (2026-05-19, battle-tested)

Proven 3-layer architecture for turning raw JSON into self-contained, single-file HTML reports. Used for Pathfinder compliance assessment visualization. Zero JavaScript, zero CSS frameworks, zero CDN external dependencies.

## Architecture

```
Raw JSON (API response)
    │
    ▼
┌─────────────┐
│  adapter.py  │  Validate shape, resolve cross-references
│              │  (condition matches, blocker→rule back-mapping)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ schemas.py   │  Frozen @dataclass view models
│              │  (ReportViewModel, BlockerEvidence, PathStepView, …)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ renderer.py  │  Python string formatting → self-contained HTML
│              │  CSS embedded in <style>, SVG inline, no <script>
└─────────────┘
       │
       ▼
  HTMLResponse
```

## Guido's Rule: Templates Never See Raw Dicts

The template/renderer receives frozen dataclasses, never mutable dicts. This prevents:
- Jinja macros accidentally modifying shared state
- KeyError from missing dict keys (caught at adapter validation)
- Three templates depending on undocumented magic dict keys

Every view model field is typed and documented. The adapter is the single place where raw JSON shape assumptions live.

## Musk's Rule: One File, Vertical Scroll, No Tabs

Tabs hide information. The user must scroll to see everything — this forces the designer to prioritize what matters most and put it at the top. A self-contained HTML file means:
- Can be saved, emailed, printed
- Opens in any browser with no server dependency
- Machine-readable audit trace in a `<details>` JSON block at the bottom

## Structure (4-section vertical layout)

```
┌─────────────────────────────────────────┐
│  ① READINESS SCORE                       │
│     Big colored banner (READY/NOT READY) │
│     Confidence bar (0-100%)              │
│     Key metrics (rules/blockers/steps)   │
├─────────────────────────────────────────┤
│  ② BLOCKERS                              │
│     Red cards, one per blocker           │
│     Expandable: why did this rule fire?  │
│     Condition match table (field/op/     │
│     expected/your-value)                 │
├─────────────────────────────────────────┤
│  ③ COMPLIANCE PATH                       │
│     Text node flow, color-coded          │
│     ✓ Done / ✗ Blocked / ▶ Here / ○ Pend│
│  ③b PATH GRAPH (SVG)                     │
│     Layered DAG: maturity_level = x-axis │
│     Same color coding as text view       │
├─────────────────────────────────────────┤
│  ④ EVIDENCE: TRIGGERED RULES             │
│     Expandable rule cards                │
│     Condition match vs user answers      │
│     Compliance refs + source doc         │
├─────────────────────────────────────────┤
│  Audit Trace (machine-readable JSON)     │
│  in collapsible <details> block          │
└─────────────────────────────────────────┘
```

## Jobs' Rule: Narrative, Not Navigation

A compliance officer opens this page and thinks "I understand this and know what to do Monday morning." That's the product. Everything else is code.

Key design principles:
- Start with the verdict (big status word), then explain why
- Blockers are actionable tasks, not red decorations
- Condition match tables show YOUR value vs EXPECTED value — side by side
- Compliance references link back to actual regulation text

## FastAPI Integration

Single endpoint with format parameter:
```
GET /v1/assessments/{id}/report?format=json   → raw JSON (existing)
GET /v1/assessments/{id}/report?format=html   → HTMLResponse (new)
```

No new routes. The JSON output is the single source of truth. The HTML is a deterministic rendering of it.

## Implementation files (Pathfinder example)

```
pathfinder/visualization/
  schemas.py   — 6 frozen @dataclass (ReportViewModel, ReadinessSummary,
                BlockerEvidence, PathStepView, RuleCard, ConditionMatch)
  adapter.py   — build_view_model(report_dict) → ReportViewModel
                + _validate_report_shape(), _build_condition_matches()
  renderer.py  — render_html(vm) → str (complete HTML page)
                + _render_readiness(), _render_blockers(), _render_path(),
                  _render_evidence()
  graph.py     — render_path_svg(steps) → str (inline SVG)
```

## Pitfalls

- **Don't start with the HTML.** Write the view model dataclasses first. Define the contracts. The HTML is trivial once the structs are honest. (Guido)
- **Don't split views into separate files.** The "integration phase" is a code smell that the views should never have been separate. One renderer, one file. (Musk)
- **Don't hand-write SVG layout for >20 nodes.** Use graphviz CLI or limit to subgraphs. Crossing minimization is a research problem, not a sprint task. (Xiaolong)
- **condition match back-mapping is fragile.** Blocker text is `rule.action.text` — match it back to the rule that produced it by exact string comparison. If two rules produce identical action.text, the first match wins.
