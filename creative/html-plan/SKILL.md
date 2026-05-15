---
name: html-plan
description: Generate self-contained HTML implementation plans with interactive timelines, milestone tracking, risk tables, dependency graphs, and task breakdowns — in the HTML Effectiveness style.
version: 1.0.0
category: creative
---

# HTML Plan — Implementation Plans as HTML

Generate self-contained `.html` files for project plans. Open directly in a browser. Replaces Gantt charts and static markdown task lists with a visual, scannable timeline.

## Trigger Conditions

- User asks for an implementation plan, project plan, roadmap, milestone plan, or task breakdown
- After a spec is done and the user wants "what's next"
- Any "how to build this" question that needs a structured timeline

## Design System

Same CSS variables as `html-spec`. See that skill for the full palette and typography tokens.

## Document Structure

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Implementation Plan — Project Name</title>
<style>/* embedded CSS */</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="eyebrow">IMPLEMENTATION PLAN · M1–M36 · 2026</div>
    <h1>Project Title</h1>
    <p class="intro">What we're building, who's building it, and when each piece lands.</p>
  </header>

  <section id="timeline">
    <div class="sec-head"><span class="idx">01</span><h2>Timeline</h2></div>
    <!-- Interactive timeline visualization -->
  </section>

  <section id="phases">
    <div class="sec-head"><span class="idx">02</span><h2>Phases</h2></div>
    <!-- Phase cards with tasks -->
  </section>

  <section id="dependencies">
    <div class="sec-head"><span class="idx">03</span><h2>Dependencies</h2></div>
    <!-- Upstream/downstream dependency graph -->
  </section>

  <section id="risks">
    <div class="sec-head"><span class="idx">04</span><h2>Risk Register</h2></div>
    <!-- Risk matrix table -->
  </section>

  <section id="deliverables">
    <div class="sec-head"><span class="idx">05</span><h2>Deliverables</h2></div>
    <!-- Deliverable table with dates and owners -->
  </section>

  <footer>
    <div class="k">DataWego</div>
    <div>Generated YYYY-MM-DD</div>
  </footer>
</div>
</body>
</html>
```

## Key Pattern: Interactive Timeline

The most important element of a plan. Use CSS-only horizontal timeline:

```css
.timeline { position: relative; padding: 40px 0; }
.timeline::before {
  content: ""; position: absolute; left: 0; right: 0; top: 55px;
  height: 4px; background: var(--g200); border-radius: 2px;
}
.timeline-phases { display: flex; gap: 0; position: relative; }
.timeline-phase {
  flex: 1; text-align: center; position: relative; padding-top: 30px;
  cursor: pointer;
}
.timeline-phase::before {
  content: ""; position: absolute; top: 47px; left: 50%;
  width: 16px; height: 16px; border-radius: 50%; background: var(--clay);
  transform: translateX(-50%); border: 3px solid var(--ivory);
  z-index: 1;
}
.timeline-phase.current::before { background: var(--slate); width: 20px; height: 20px; top: 45px; }
.timeline-phase.future::before { background: var(--g300); }
.timeline-phase .phase-label { font-family: var(--mono); font-size: 11px; color: var(--g500); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.timeline-phase .phase-name { font-family: var(--serif); font-size: 16px; font-weight: 500; }
.timeline-phase .phase-date { font-size: 12px; color: var(--g500); margin-top: 4px; }
.timeline-phase:hover .phase-name { color: var(--clay); }
```

```html
<div class="timeline">
  <div class="timeline-phases">
    <div class="timeline-phase current">
      <div class="phase-label">Phase 0</div>
      <div class="phase-name">Formalization Freeze</div>
      <div class="phase-date">M1–M3</div>
    </div>
    <div class="timeline-phase">
      <div class="phase-label">Phase 1</div>
      <div class="phase-name">Core Engine</div>
      <div class="phase-date">M4–M9</div>
    </div>
    <div class="timeline-phase future">
      <div class="phase-label">Phase 2</div>
      <div class="phase-name">API + MVP</div>
      <div class="phase-date">M10–M15</div>
    </div>
    <!-- more phases -->
  </div>
</div>
```

For detailed phase expansion, use CSS accordion (no JS needed):

```html
<details open>
  <summary style="cursor:pointer; padding:16px 0; font-family:var(--serif); font-size:20px; font-weight:500; border-bottom:1.5px solid var(--g200); list-style:none;">
    <span style="font-family:var(--mono);font-size:13px;color:var(--clay);margin-right:12px;">Phase 1</span> Core Engine Development
    <span style="float:right;font-family:var(--mono);font-size:12px;color:var(--g500);">M4–M9</span>
  </summary>
  <div style="padding:20px 0 20px 36px;">
    <table>
      <tr><td style="width:80px;"><span class="badge badge-high">P0</span></td><td><strong>Graph engine</strong></td><td>Dijkstra solver on DAG</td><td>M6</td></tr>
      <tr><td style="width:80px;"><span class="badge badge-high">P0</span></td><td><strong>Constraint checker</strong></td><td>WP8 rule evaluator</td><td>M7</td></tr>
      <tr><td style="width:80px;"><span class="badge badge-medium">P1</span></td><td><strong>Questionnaire engine</strong></td><td>Dynamic form from JSON schema</td><td>M8</td></tr>
    </table>
  </div>
</details>
```

## Dependency Graph (Inline SVG)

```html
<svg viewBox="0 0 900 300" style="width:100%; max-width:900px;">
  <!-- Upstream nodes (left) -->
  <rect x="20" y="40" width="140" height="50" rx="8" fill="var(--paper)" stroke="var(--clay)" stroke-width="2"/>
  <text x="90" y="70" text-anchor="middle" font-size="12" font-family="system-ui" fill="var(--slate)">WP3 Roadmap</text>

  <!-- Our node (center) -->
  <rect x="360" y="120" width="180" height="60" rx="8" fill="var(--oat)" stroke="var(--slate)" stroke-width="2"/>
  <text x="450" y="145" text-anchor="middle" font-size="13" font-family="system-ui" font-weight="600" fill="var(--slate)">Pathfinder</text>
  <text x="450" y="165" text-anchor="middle" font-size="11" font-family="monospace" fill="var(--g500)">WP4 Engine</text>

  <!-- Downstream nodes (right) -->
  <rect x="720" y="180" width="140" height="50" rx="8" fill="var(--paper)" stroke="var(--olive)" stroke-width="2"/>
  <text x="790" y="210" text-anchor="middle" font-size="12" font-family="system-ui" fill="var(--slate)">AI Factories</text>

  <!-- Dependency arrows -->
  <line x1="160" y1="65" x2="360" y2="135" stroke="var(--g500)" stroke-width="2" marker-end="url(#arrow)" stroke-dasharray="6 3"/>
  <line x1="540" y1="150" x2="720" y2="195" stroke="var(--g500)" stroke-width="2" marker-end="url(#arrow)"/>
</svg>
```

## Risk Register

Same pattern as html-spec — badge-based risk matrix:

```html
<table class="risk-matrix">
  <thead><tr><th width="40%">Risk</th><th>Probability</th><th>Impact</th><th width="35%">Mitigation</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>WP3 delivers PDF instead of structured data</strong></td>
      <td><span class="badge badge-high">High</span></td>
      <td><span class="badge badge-critical">Critical</span></td>
      <td>Require JSON schema sign-off by M2; refuse to start without it</td>
    </tr>
  </tbody>
</table>
```

## Interactive Priority Filter

Let users filter tasks by priority:

```html
<div style="margin:20px 0; display:flex; gap:8px;">
  <button class="filter-btn active" onclick="filterTasks('all')" style="padding:6px 14px; border:1.5px solid var(--g300); border-radius:999px; background:var(--paper); cursor:pointer; font-size:12px;">All</button>
  <button class="filter-btn" onclick="filterTasks('p0')" style="padding:6px 14px; border:1.5px solid var(--g300); border-radius:999px; background:var(--paper); cursor:pointer; font-size:12px;">🔴 P0</button>
  <button class="filter-btn" onclick="filterTasks('p1')" style="padding:6px 14px; border:1.5px solid var(--g300); border-radius:999px; background:var(--paper); cursor:pointer; font-size:12px;">🟡 P1</button>
  <button class="filter-btn" onclick="filterTasks('p2')" style="padding:6px 14px; border:1.5px solid var(--g300); border-radius:999px; background:var(--paper); cursor:pointer; font-size:12px;">🟢 P2</button>
</div>
<script>
function filterTasks(pri) {
  document.querySelectorAll('.task-row').forEach(row => {
    row.style.display = (pri === 'all' || row.dataset.priority === pri) ? '' : 'none';
  });
  document.querySelectorAll('.filter-btn').forEach(b => b.style.background = 'var(--paper)');
  event.target.style.background = 'var(--g100)';
}
</script>
```

## Pitfalls

- **Don't fake the timeline**: If you don't know exact dates, show relative ordering (phases, not calendar months).
- **Accordion fatigue**: Don't put EVERY task in an accordion. Show the top 3-5 per phase in the open state.
- **Dependency graph must be honest**: If WP3 is really a single point of failure, show it visually. Don't prettify risk.
- **One file**: No external JS, no chart libraries, no CDN CSS. Timeline is CSS-only.
