---
name: html-review
description: Generate self-contained HTML code review documents — annotated diffs, PR writeups, module understanding maps, and architecture review findings — in the HTML Effectiveness style. Spatial layout replaces linear terminal scrolling.
version: 1.0.0
category: creative
---

# HTML Review — Code Review as Spatial HTML

Generate self-contained `.html` files for code reviews, PR writeups, and code understanding. Diffs and call-graphs are spatial information — HTML renders them that way.

## Trigger Conditions

- User asks for a code review, PR review, PR writeup, or code understanding document
- After reading code and the user wants a visual summary
- Architecture or design review that needs annotated diagrams

## Document Types

### Type A: Annotated Diff (for PR review)

```
┌──────────────────────────────────────────────────┐
│  masthead: PR title, branch, stats               │
├──────────────────────────────────────────────────┤
│  Summary section: what changed, why              │
├──────────────┬───────────────────────────────────┤
│  File tree   │  Diff view with annotation        │
│  (sticky)    │  margin notes in clay color       │
│              │  severity tags per change         │
│              │  jump links between files         │
└──────────────┴───────────────────────────────────┘
```

### Type B: PR Writeup (author explaining their work)

```
┌──────────────────────────────────────────────────┐
│  masthead: Motivation, Before/After              │
├──────────────────────────────────────────────────┤
│  File-by-file tour with WHY (not just what)      │
│  Each file: rationale + key change + risk note   │
│  Where to focus review highlighted               │
├──────────────────────────────────────────────────┤
│  Testing strategy / How to verify                │
└──────────────────────────────────────────────────┘
```

### Type C: Module Understanding Map

```
┌──────────────────────────────────────────────────┐
│  masthead: Module name, files, key stats         │
├──────────────────────────────────────────────────┤
│  Box-and-arrow call graph (SVG)                  │
│  Each box = file/module, arrows = imports/calls  │
│  Color-coded by concern                          │
├──────────────────────────────────────────────────┤
│  Per-file breakdown (collapsible)                │
│  Public API surface highlighted                  │
│  "If you change X, check Y" callouts             │
└──────────────────────────────────────────────────┘
```

## Design System

Same CSS variables as `html-spec`. Additional review-specific styles:

```css
/* Diff styling */
.diff-add { background: #DCFCE7; color: #166534; }
.diff-remove { background: #FEE2E2; color: #991B1B; }
.diff-context { color: var(--g500); }

/* Severity badges for review findings */
.sev-critical { background: #FEE2E2; color: #991B1B; border-color: #FCA5A5; }
.sev-major { background: #FEF3C7; color: #92400E; border-color: #FCD34D; }
.sev-minor { background: #F0FDF4; color: #166534; border-color: #86EFAC; }
.sev-note { background: var(--g100); color: var(--g700); border-color: var(--g300); }

/* Annotation margin note */
.annotation {
  border-left: 3px solid var(--clay);
  padding: 4px 0 4px 16px;
  margin: 8px 0;
  font-size: 13px;
  color: var(--g700);
}

/* File tree sidebar */
.file-tree {
  position: sticky; top: 20px;
  font-family: var(--mono); font-size: 12px;
  line-height: 2;
}
.file-tree .active { color: var(--clay); font-weight: 600; }
.file-tree .added::before { content: "+ "; color: #166534; }
.file-tree .modified::before { content: "~ "; color: #92400E; }
.file-tree .deleted::before { content: "− "; color: #991B1B; }
```

## Annotated Diff Pattern

Two-column layout: sticky file tree on left, diff on right:

```html
<div style="display:grid; grid-template-columns:220px 1fr; gap:40px; margin-top:40px;">
  <nav class="file-tree">
    <div class="active">src/core/solver.py <span style="color:var(--g500);">+34 −12</span></div>
    <div>src/api/routes.py <span style="color:var(--g500);">+18 −4</span></div>
    <div>tests/test_solver.py <span style="color:var(--g500);">+62 −0</span></div>
  </nav>
  <div>
    <h3 style="font-family:var(--mono);font-size:14px;margin:0 0 16px;">src/core/solver.py</h3>

    <!-- Annotation before the diff -->
    <div class="annotation">
      <strong>🔍 Why this change:</strong> The original solver assumed the graph was connected.
      WP3 roadmap may have isolated nodes. Added BFS fallback with warning.
      <br><span style="font-size:11px;color:var(--g500);">Review focus: error handling in _find_component()</span>
    </div>

    <pre style="background:var(--paper);border:1.5px solid var(--g200);"><code><span class="diff-context"> 89  def solve(self, state):</span>
<span class="diff-context"> 90      """Find shortest path under constraints."""</span>
<span class="diff-remove"> 91 -    path = nx.shortest_path(self.graph, start, end)</span>
<span class="diff-add"> 91 +    path = self._shortest_path_or_fallback(start, end)</span>
<span class="diff-context"> 92      return self._path_to_recommendations(path)</span></code></pre>
  </div>
</div>
```

## Module Understanding Map

Inline SVG call graph with per-file details in accordions:

```html
<svg viewBox="0 0 800 350" style="width:100%; max-width:800px;">
  <!-- Public API surface -->
  <rect x="300" y="20" width="200" height="50" rx="8" fill="var(--clay)" opacity="0.15" stroke="var(--clay)" stroke-width="2"/>
  <text x="400" y="50" text-anchor="middle" font-size="13" font-family="system-ui" font-weight="600" fill="var(--clay)">Public API</text>

  <!-- Core engine -->
  <rect x="320" y="100" width="160" height="50" rx="8" fill="var(--paper)" stroke="var(--slate)" stroke-width="2"/>
  <text x="400" y="130" text-anchor="middle" font-size="12" font-family="monospace" fill="var(--slate)">solver.py</text>

  <!-- Dependencies -->
  <rect x="80" y="220" width="140" height="40" rx="6" fill="var(--g100)" stroke="var(--g300)" stroke-width="1.5"/>
  <text x="150" y="245" font-size="11" font-family="monospace" fill="var(--g700)">graph.py</text>

  <!-- Arrows -->
  <line x1="400" y1="150" x2="400" y2="100" stroke="var(--clay)" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="150" y1="220" x2="320" y2="125" stroke="var(--g500)" stroke-width="1.5" stroke-dasharray="4 3"/>
</svg>

<details open>
  <summary style="cursor:pointer;font-family:var(--mono);font-size:14px;padding:12px 0;">src/core/solver.py — Pathfinding Engine</summary>
  <table style="margin-left:20px;">
    <tr><td style="width:50px;"><span class="badge badge-high">PUBLIC</span></td><td><code>PathfinderSolver.solve(state) → PathResult</code></td></tr>
    <tr><td style="width:50px;"><span class="badge badge-medium">INTERNAL</span></td><td><code>_shortest_path_or_fallback(start, end)</code></td></tr>
    <tr><td style="width:50px;"><span class="badge badge-low">PRIVATE</span></td><td><code>_is_compliant(state, node)</code></td></tr>
  </table>
  <p style="margin-left:20px;font-size:13px;color:var(--g700);">⚠️ If you change <code>_is_compliant</code>, also check <code>compliance.py</code> and <code>test_compliance.py</code>.</p>
</details>
```

## Finding Callout Pattern

Each review finding gets a severity-tagged card:

```html
<div style="border:1.5px solid var(--g200); border-radius:10px; padding:16px 20px; margin:12px 0; border-left:4px solid var(--clay);">
  <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px;">
    <span class="sev-major" style="font-family:var(--mono);font-size:10px;padding:3px 8px;border-radius:999px;border:1px solid;">MAJOR</span>
    <strong style="font-size:14px;">Undefined behavior when graph is disconnected</strong>
  </div>
  <div style="font-size:13px;color:var(--g700);">
    <code>nx.shortest_path()</code> raises <code>NetworkXNoPath</code> on disconnected components.
    The solver should catch this and return a diagnostic instead of crashing.
    <br><strong>Fix:</strong> Add try/except with BFS fallback to find nearest reachable node.
  </div>
  <div style="margin-top:10px;font-size:11px;color:var(--g500);font-family:var(--mono);">
    src/core/solver.py:89 &nbsp;|&nbsp; Severity: Major &nbsp;|&nbsp; Effort: 30min
  </div>
</div>
```

## Pitfalls

- **Don't fake the diff**: If you don't have the actual diff, show a code understanding map (Type C) instead.
- **Review findings must be actionable**: Each finding = what's wrong + why it matters + how to fix + estimated effort.
- **Don't review style**: Review logic, architecture, correctness. Style is for linters.
- **File tree must stay visible**: Use `position:sticky` so the reader doesn't lose context while scrolling.
