---
name: html-report
description: Generate self-contained HTML reports — project status, meeting summaries, analysis reports, research findings, council debate syntheses — in the HTML Effectiveness style. Cards, metrics, and visual hierarchy replace walls of text.
version: 1.0.0
category: creative
---

# HTML Report — Beautiful Project Reports

Generate self-contained `.html` files for any kind of report. Open directly in a browser. Every report is a single file with embedded CSS. Designed for reading, not skimming.

## Trigger Conditions

- User asks for a report, summary, analysis, or findings document
- After a multi-agent debate or council session (capture the synthesis)
- Project status updates, milestone reviews, or post-mortems
- Research summaries with findings and recommendations
- Any "write this up" request where the output will be read by humans

## Document Types

### Type A: Status Report (dashboard-like)
```
┌──────────────────────────────────────────────┐
│  masthead: period, project, health indicator │
├──────────┬──────────┬──────────┬─────────────┤
│  Metric  │  Metric  │  Metric  │  Metric     │
│  (big #) │  (big #) │  (big #) │  (big #)   │
├──────────┴──────────┴──────────┴─────────────┤
│  Phase progress bars + key accomplishments   │
├──────────────────────────────────────────────┤
│  Risk heat map (compact)                     │
├──────────────────────────────────────────────┤
│  Next period: top 3 priorities               │
└──────────────────────────────────────────────┘
```

### Type B: Analysis Report (findings + recommendations)
```
┌──────────────────────────────────────────────┐
│  masthead: title, scope, date                │
├──────────────────────────────────────────────┤
│  Executive summary (3 sentences max)         │
├──────────────────────────────────────────────┤
│  Finding cards (icon + severity + detail)    │
├──────────────────────────────────────────────┤
│  Recommendation table (actionable)           │
├──────────────────────────────────────────────┤
│  Appendix: data sources, methodology         │
└──────────────────────────────────────────────┘
```

### Type C: Debate Synthesis (multi-perspective)
```
┌──────────────────────────────────────────────┐
│  masthead: topic, participants, verdict      │
├──────────┬──────────┬──────────┬─────────────┤
│  Position│  Position│  Position│  Position   │
│  Card    │  Card    │  Card    │  Card       │
├──────────┴──────────┴──────────┴─────────────┤
│  Consensus summary + dissenting views        │
├──────────────────────────────────────────────┤
│  Action items (who does what by when)        │
└──────────────────────────────────────────────┘
```

## Design System

Same CSS variables as `html-spec`. Additional report-specific styles:

```css
/* Metric cards */
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 32px 0; }
.metric-card {
  background: var(--paper); border: 1.5px solid var(--g200);
  border-radius: 12px; padding: 20px 24px;
}
.metric-value { font-family: var(--serif); font-size: 36px; font-weight: 500; line-height: 1; margin-bottom: 6px; }
.metric-label { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--g500); }
.metric-card.good { border-left: 4px solid var(--olive); }
.metric-card.warn { border-left: 4px solid #D97757; }
.metric-card.bad  { border-left: 4px solid #991B1B; }

/* Progress bar */
.progress-bar { height: 8px; background: var(--g200); border-radius: 4px; margin: 8px 0; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; background: var(--clay); transition: width 0.6s ease; }
.progress-fill.green { background: var(--olive); }

/* Finding cards */
.finding {
  border: 1.5px solid var(--g200); border-radius: 10px;
  padding: 20px 24px; margin: 14px 0;
  border-left: 4px solid var(--clay);
}
.finding.critical { border-left-color: #991B1B; background: #FFF5F5; }
.finding.positive { border-left-color: var(--olive); background: #F7FAF5; }
.finding h3 { font-size: 16px; margin: 0 0 8px; }
.finding .source { font-family: var(--mono); font-size: 11px; color: var(--g500); margin-top: 10px; }

/* Position cards (for debate synthesis) */
.position-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin: 24px 0; }
.position-card {
  background: var(--paper); border: 1.5px solid var(--g200);
  border-radius: 12px; padding: 20px; position: relative;
}
.position-card .avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--g100); border: 2px solid var(--g300);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--mono); font-size: 14px; font-weight: 600;
  margin-bottom: 10px;
}
.position-card .quote { font-size: 14px; font-style: italic; color: var(--g700); margin: 10px 0; padding-left: 12px; border-left: 3px solid var(--oat); }

/* Consensus box */
.consensus {
  background: linear-gradient(135deg, #F7FAF5, #EDF3E8);
  border: 1.5px solid var(--olive);
  border-radius: 12px; padding: 24px 28px; margin: 32px 0;
}
.consensus h3 { color: var(--olive); margin: 0 0 10px; }

/* Action items */
.action-item {
  display: flex; gap: 16px; align-items: baseline;
  padding: 12px 0; border-bottom: 1px solid var(--g200);
}
.action-item .who { font-family: var(--mono); font-size: 12px; color: var(--clay); min-width: 100px; }
.action-item .what { flex: 1; font-size: 14px; }
.action-item .when { font-family: var(--mono); font-size: 11px; color: var(--g500); white-space: nowrap; }
```

## Status Report Pattern

```html
<section id="status">
  <div class="sec-head"><span class="idx">01</span><h2>Current Status</h2></div>
  <div class="metrics">
    <div class="metric-card good">
      <div class="metric-value">67%</div>
      <div class="metric-label">Overall Progress</div>
    </div>
    <div class="metric-card warn">
      <div class="metric-value">3</div>
      <div class="metric-label">Open Risks</div>
    </div>
    <div class="metric-card good">
      <div class="metric-value">8/12</div>
      <div class="metric-label">Milestones Hit</div>
    </div>
  </div>

  <h3 style="font-family:var(--serif);font-size:18px;">Phase Progress</h3>
  <div style="margin:16px 0;">
    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
      <span>Phase 0: Formalization</span><span style="color:var(--olive);">100%</span>
    </div>
    <div class="progress-bar"><div class="progress-fill green" style="width:100%"></div></div>
  </div>
  <div style="margin:16px 0;">
    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
      <span>Phase 1: Core Engine</span><span style="color:var(--clay);">60%</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" style="width:60%"></div></div>
  </div>
</section>
```

## Findings + Recommendations Pattern

```html
<section id="findings">
  <div class="sec-head"><span class="idx">02</span><h2>Key Findings</h2></div>

  <div class="finding critical">
    <h3>🚨 WP3 roadmap format not yet confirmed</h3>
    <p>CHARITE has not committed to JSON output. Risk of PDF-only delivery would block all downstream work.</p>
    <div class="source">Source: WP3 meeting, 2026-05-10 · Owner: Feng Ge</div>
  </div>

  <div class="finding">
    <h3>📋 SHAIPED audit reveals reusable rule engine</h3>
    <p>Lu Zhao's prior project has a YAML-based rule format that can be adapted for Pathfinder. Estimated 40% reuse.</p>
    <div class="source">Source: SHAIPED code review · Owner: Xiaolong</div>
  </div>

  <div class="finding positive">
    <h3>✅ All council members agree on monolith architecture</h3>
    <p>9/9 seats: no microservices, no K8s, no Neo4j. Docker Compose + PostgreSQL + FastAPI.</p>
    <div class="source">Source: Council debate 2026-05-13</div>
  </div>
</section>

<section id="recommendations">
  <div class="sec-head"><span class="idx">03</span><h2>Recommendations</h2></div>
  <table>
    <thead><tr><th>#</th><th>Action</th><th>Owner</th><th>By</th><th>Priority</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Send formalization requirements to WP3 Lead</td><td>Feng Ge</td><td>M1 W2</td><td><span class="badge badge-critical">P0</span></td></tr>
      <tr><td>2</td><td>Schedule SHAIPED code walkthrough with Lu Zhao</td><td>Xiaolong</td><td>M1 W1</td><td><span class="badge badge-high">P1</span></td></tr>
      <tr><td>3</td><td>Draft subcontract with scope boundaries and payment terms</td><td>Feng Ge</td><td>M1 W3</td><td><span class="badge badge-high">P1</span></td></tr>
    </tbody>
  </table>
</section>
```

## Debate Synthesis Pattern (for council outputs)

```html
<section id="positions">
  <div class="sec-head"><span class="idx">01</span><h2>Council Positions</h2></div>
  <div class="position-cards">
    <div class="position-card">
      <div class="avatar">M</div>
      <strong>Musk · CVO</strong>
      <div class="quote">"You're building a state transition function, not a tool. pathfinder.solve(state, target) → Path."</div>
      <div style="font-size:12px;color:var(--g500);">Core: Truth machine, not presentation layer</div>
    </div>
    <!-- more cards -->
  </div>
</section>

<section>
  <div class="sec-head"><span class="idx">02</span><h2>Consensus</h2></div>
  <div class="consensus">
    <h3>9/9 Seats Agree</h3>
    <ul style="margin:0;padding-left:20px;font-size:14px;line-height:2;">
      <li>Pathfinder = constrained graph search + questionnaire, not a platform</li>
      <li>Monolith FastAPI + PostgreSQL. No K8s, no microservices, no Neo4j.</li>
      <li>M3 formalization freeze is the go/no-go gate.</li>
      <li>Rules externalized as YAML, hot-loadable, non-programmer-reviewable.</li>
    </ul>
  </div>
</section>

<section>
  <div class="sec-head"><span class="idx">03</span><h2>Action Items</h2></div>
  <div class="action-item"><span class="who">Feng Ge</span><span class="what">Draft subcontract with scope boundaries</span><span class="when">M1 W3</span></div>
  <div class="action-item"><span class="who">Linus+Xiaolong</span><span class="what">Set up project scaffold (Docker, CI/CD, repo)</span><span class="when">M1 W1</span></div>
  <div class="action-item"><span class="who">Guido+Dijkstra</span><span class="what">Define WP2/3/8 data interface schemas</span><span class="when">M1 W2</span></div>
</section>
```

## When to Use Each Pattern

| Report Type | Key Patterns | Interactive? |
|------------|-------------|--------------|
| Status Report | Metric cards, progress bars, phase summaries | Expandable phase details |
| Analysis Report | Finding cards (severity-coded), recommendation table | Collapsible methodology appendix |
| Debate Synthesis | Position cards grid, consensus box, action items | None needed |
| Post-mortem | Timeline, what-went-well/wrong cards, lessons learned | None needed |
| Research Summary | Key insight cards, data source table, confidence ratings | Filter by confidence |

## Pitfalls

- **Data-to-HTML pipeline pattern**: When converting API JSON to self-contained HTML reports, use the view-model contract layer: JSON → adapter (validates, resolves cross-refs) → frozen @dataclass → renderer (string formatting). Templates must never receive raw dicts. Full pattern + schema examples in `references/data-to-html-pipeline.md`.

- **Metric cards need context**: "67% complete" means nothing without "target was 70%". Add trend arrows (↑↓→).
- **Finding cards need severity**: Every finding must be tagged. Reader should know in 2 seconds what to worry about.
- **Consensus must include dissent**: If 8/9 agree, show the 1 dissent. It's often the most valuable perspective.
- **Action items need owners**: No owner, no action. Every item gets a person and a date.
