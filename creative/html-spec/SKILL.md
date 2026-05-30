---
name: html-spec
description: Generate self-contained HTML specification documents (architecture specs, API specs, data schemas, design decisions) in the HTML Effectiveness style — beautiful, scannable, with interactive diagrams where helpful.
version: 1.0.0
category: creative
---

# HTML Spec — Beautiful Technical Specifications

Generate self-contained `.html` files for technical specifications. Open directly in a browser — no build step, no dependencies. Every spec is a single file with embedded CSS.

## Trigger Conditions

- User asks for a spec, specification, architecture document, API doc, schema doc, design decision record, or technical proposal
- User says "make it HTML" or "make it beautiful" or references "HTML Effectiveness"
- After a major architectural decision that needs documenting

## Design System (CSS Variables)

Always embed these CSS variables in every spec:

```css
:root {
  --ivory:  #FAF9F5;
  --paper:  #FFFFFF;
  --slate:  #141413;
  --clay:   #D97757;
  --clay-d: #B85C3E;
  --oat:    #E3DACC;
  --olive:  #788C5D;
  --g100:   #F0EEE6;
  --g200:   #E6E3DA;
  --g300:   #D1CFC5;
  --g500:   #87867F;
  --g700:   #3D3D3A;
  --serif: ui-serif, Georgia, "Times New Roman", Times, serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace;
}
```

## Document Structure

Every spec follows this skeleton:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SPEC TITLE — Project Name</title>
<style>/* embedded CSS */</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="eyebrow">SPECIFICATION · STATUS · DATE</div>
    <h1>Title</h1>
    <p class="intro">One-paragraph summary of what this spec covers and why.</p>
  </header>

  <section id="overview">
    <div class="sec-head"><span class="idx">01</span><h2>Overview</h2></div>
    <!-- content -->
  </section>

  <section id="architecture">
    <div class="sec-head"><span class="idx">02</span><h2>Architecture</h2></div>
    <!-- Architecture diagram (inline SVG) + description -->
  </section>

  <section id="decisions">
    <div class="sec-head"><span class="idx">03</span><h2>Key Decisions</h2></div>
    <!-- Decision table or cards -->
  </section>

  <section id="schema">
    <div class="sec-head"><span class="idx">04</span><h2>Data Schema</h2></div>
    <!-- Schema in formatted code blocks or interactive tables -->
  </section>

  <section id="api">
    <div class="sec-head"><span class="idx">05</span><h2>API Design</h2></div>
    <!-- Endpoint table + request/response examples -->
  </section>

  <section id="risks">
    <div class="sec-head"><span class="idx">06</span><h2>Risks & Tradeoffs</h2></div>
    <!-- Risk matrix -->
  </section>

  <footer>
    <div class="k">DataWego</div>
    <div>Generated YYYY-MM-DD · <a href="#">source</a></div>
  </footer>
</div>
</body>
</html>
```

## Key CSS Patterns

### Masthead (always include)
```css
header.masthead { padding: 80px 0 56px; border-bottom: 1.5px solid var(--g300); margin-bottom: 12px; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--g500); margin-bottom: 18px; }
h1 { font-family: var(--serif); font-weight: 500; font-size: clamp(38px, 5.4vw, 62px); line-height: 1.06; letter-spacing: -0.018em; margin: 0 0 8px; }
.intro { font-size: 16.5px; color: var(--g700); max-width: 620px; margin: 22px 0 0; }
```

### Section headers with index numbers
```css
section { margin-top: 72px; scroll-margin-top: 28px; }
.sec-head { display: flex; align-items: baseline; gap: 16px; margin-bottom: 10px; }
.sec-head .idx { font-family: var(--mono); font-size: 13px; color: var(--clay); font-weight: 600; width: 34px; flex-shrink: 0; }
.sec-head h2 { font-family: var(--serif); font-weight: 500; font-size: 27px; margin: 0; letter-spacing: -0.012em; }
```

### Code blocks (inline and block)
```css
code { font-family: var(--mono); font-size: 0.88em; background: var(--g100); padding: 2px 6px; border-radius: 4px; }
pre { background: var(--slate); color: var(--ivory); padding: 20px 24px; border-radius: 10px; overflow-x: auto; font-size: 13.5px; line-height: 1.6; }
pre code { background: none; padding: 0; border-radius: 0; color: inherit; }
```

### Decision tables
```css
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead th { text-align: left; font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--g500); padding: 0 0 10px; border-bottom: 1.5px solid var(--g300); }
tbody td { padding: 12px 0; border-bottom: 1px solid var(--g200); vertical-align: top; }
tr:last-child td { border-bottom: none; }
```

### Architecture diagrams (inline SVG)
Use inline SVG for architecture diagrams. Keep them simple — boxes, arrows, labels. Use the CSS variable colors directly: `var(--clay)`, `var(--olive)`, `var(--oat)`, `var(--slate)`.

**Distinguish REQUEST vs DATA flow.** HTTP request direction ≠ data direction. Architecture specs must show both:
- REQUEST arrows (thin, gray): who initiates the HTTP call
- DATA arrows (bold, colored): how data flows upstream→downstream and back to client
- WRITE arrows (dashed): persistence to database/cache

A diagram that only shows request arrows makes it look like data flows into services and never comes out. Complete the round-trip: client → server → upstream → server → client. See `architecture-diagram` skill for the full pattern.

```html
<svg viewBox="0 0 800 400" style="width:100%; max-width:800px;">
  <!-- Box: User -->
  <rect x="20" y="160" width="120" height="60" rx="8" fill="var(--paper)" stroke="var(--g300)" stroke-width="2"/>
  <text x="80" y="195" text-anchor="middle" font-family="system-ui" font-size="13" fill="var(--slate)">User</text>
  <!-- Arrow -->
  <line x1="140" y1="190" x2="200" y2="190" stroke="var(--clay)" stroke-width="2" marker-end="url(#arrow)"/>
  <!-- ... more elements ... -->
</svg>
```

### Risk matrix
```html
<table class="risk-matrix">
  <thead><tr><th>Risk</th><th>Probability</th><th>Impact</th><th>Mitigation</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>WP3 delivers PDF not JSON</strong></td>
      <td><span class="badge badge-high">High</span></td>
      <td><span class="badge badge-critical">Critical</span></td>
      <td>Require JSON schema by M3</td>
    </tr>
  </tbody>
</table>
```

```css
.badge { font-family: var(--mono); font-size: 10px; padding: 3px 8px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em; }
.badge-high { background: #FDE8E0; color: var(--clay-d); }
.badge-critical { background: #FED7D7; color: #9B2C2C; }
.badge-medium { background: #FEF3C7; color: #92400E; }
.badge-low { background: #DCFCE7; color: #166534; }
```

## Interactive Elements

### Collapsible sections (for long schemas or code blocks)
```html
<details>
  <summary style="cursor:pointer; font-family:var(--mono); font-size:13px; color:var(--clay); padding:8px 0;">Show schema SQL</summary>
  <pre><code>CREATE TABLE ...</code></pre>
</details>
```

### Tab navigation (for comparing alternatives)
```html
<style>
.tabs { display: flex; gap: 0; margin-bottom: 0; }
.tab { padding: 10px 20px; cursor: pointer; border: 1.5px solid var(--g300); border-bottom: none; border-radius: 8px 8px 0 0; background: var(--g100); font-size: 13px; }
.tab.active { background: var(--paper); border-color: var(--clay); color: var(--clay); }
.tab-content { display: none; padding: 20px; border: 1.5px solid var(--g300); border-radius: 0 8px 8px 8px; }
.tab-content.active { display: block; }
</style>
<script>
function switchTab(evt, tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  evt.target.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}
</script>
```

### Scrollable architecture diagram
```html
<div style="overflow-x:auto; padding:20px 0;">
  <svg viewBox="0 0 1200 400" style="min-width:900px;">
    <!-- wide diagram -->
  </svg>
</div>
```

## When to Use Each Pattern

| Document Type | Sections to Include | Interactive? |
|--------------|-------------------|--------------|
| Architecture Spec | Overview, Architecture (SVG), Decisions, Data Flow | Tabs for alternative architectures |
| API Spec | Overview, Endpoints table, Request/Response, Auth, Errors | Collapsible examples |
| Data Schema | Overview, ER Diagram (SVG), Table definitions, Migrations | Collapsible SQL |
| ADR (Decision Record) | Context, Decision, Alternatives (tabs), Consequences | Tabs for alternatives |
| Tech Stack Spec | Overview, Stack table, Rationale per layer, Dependencies | None needed |

## JSON → HTML via Contract Layer

When generating HTML from an existing API JSON output (not writing a spec from scratch), use the Guido contract-layer stack: `schemas.py` (frozen dataclasses) → `adapter.py` (validate + transform) → `renderer.py` (dataclass → HTML). Full pattern in `references/json-to-html-contract-layer.md`.

## ASCII Data Flow Diagrams

When drawing data flow in `<pre><code>` blocks, use a 3-arrow convention to distinguish REQUEST from DATA from WRITE:

```
[REQ]   ──→  thin  = HTTP request (who initiates the call)
[DATA]  ══►  bold  = data flow (upstream → downstream)
[WRITE] - -→ dashed = database write
```

Key rule: arrows show **data flow direction**, not HTTP call direction. Mock/upstream services are data SOURCES — arrows point FROM upstream TO downstream. Even though Backend initiates the HTTP GET, the data flows Mock → Backend → Client.

```
RIGHT:  Mock ══[DATA]══► Backend ──[DATA]──► Client
WRONG:  Backend ──[REQ]──► Mock   (shows HTTP direction, not data flow)
```

Show the complete round-trip: Client → Backend → Mock (REQUEST chain), then Mock → Backend → Client (DATA return chain). A diagram that only shows half the flow (data in, nothing out) looks like data is trapped in the system.

## Pitfalls

- **ALWAYS use this skill FIRST for any HTML document.** Do not hand-write HTML from scratch. The user will notice missing sections, wrong styling, and raw markdown dumped into `<body>`. If you start with raw HTML and the user asks "有没有用到html的skill?", you've already lost time. Load this skill, use the exact skeleton structure (masthead + numbered sections + footer), and apply the CSS variable palette.
- **Don't over-interact**: Not every spec needs tabs and collapsible. A clean static layout that reads like a magazine is often better.
- **Keep SVG diagrams simple**: Boxes, arrows, labels. No gradients, no shadows, no 3D.
- **One file, no external dependencies**: No CDN fonts, no JS frameworks, no CSS imports. Everything inline.
- **Test in browser**: Always remind the user to open the `.html` in a browser.
- **Print-friendly**: Use `@media print` to hide interactive elements and adjust colors for paper.
- **Deployment accuracy (critical)**: When the spec describes a Docker/deployment architecture, be surgically precise about container boundaries. Never write "single Docker container" as a lazy shorthand.
- **read_file content handling**: `read_file` returns content with line number prefixes (e.g. `"   123|code"`). Always strip these before embedding in HTML. Use `re.sub(r'^\s*\d+\|', '', content, flags=re.MULTILINE)` or read via terminal `cat` for clean output.
- **Markdown → HTML conversion**: When converting existing markdown to HTML, don't dump raw MD into `<body>`. Parse sections manually or use the html-spec skeleton to rebuild proper sections with the skill's CSS classes, badges, and table styling.

- **Don't over-interact**: Not every spec needs tabs and collapsible. A clean static layout that reads like a magazine is often better.
- **Keep SVG diagrams simple**: Boxes, arrows, labels. No gradients, no shadows, no 3D. The information is what matters.
- **One file, no external dependencies**: No CDN fonts, no JS frameworks, no CSS imports. Everything inline.
- **Test in browser**: Always remind the user to open the `.html` in a browser. The agent can't see it — the user must.
- **Print-friendly**: Use `@media print` to hide interactive elements and adjust colors for paper.
- **Deployment accuracy (critical)**: When the spec describes a Docker/deployment architecture, be surgically precise about container boundaries. Never write "single Docker container" as a lazy shorthand for "Docker Compose single-node deployment." Docker best practice is one process per container — if PostgreSQL, the API server, and nginx are separate services, they belong in separate containers within the same docker-compose.yml. A spec that says "single container" when the design is multi-container will cause the user to lose confidence in the entire document. Always generate the actual deployable files (docker-compose.yml, Dockerfiles, nginx.conf, .env.example) alongside the prose spec and reference them by path. See `references/docker-compose-multi-container.md` for the canonical pattern.
- **For data-dense reports (not prose specs)**, use the view-model rendering pattern: frozen dataclass schemas → adapter → self-contained HTML. Don't hand-write HTML for every data field. Pattern documented in `references/view-model-html-rendering.md`.
- **NEVER inject raw Markdown into HTML body.** This session: Demi's EHDS-BioChem plan was generated by concatenating raw MD content into `<body>` — including `read_file`'s line-number prefixes (`   42|text`). The HTML rendered as one wall of unformatted text. Instead: (a) use `terminal cat` to read clean MD, (b) convert to HTML elements with Python regex, (c) apply html-spec CSS classes. See `references/markdown-to-html-conversion.md`.
- **Deployment accuracy (critical)**: When the spec describes a Docker/deployment architecture, be surgically precise about container boundaries. Never write "single Docker container" as a lazy shorthand for "Docker Compose single-node deployment." Docker best practice is one process per container — if PostgreSQL, the API server, and nginx are separate services, they belong in separate containers within the same docker-compose.yml. A spec that says "single container" when the design is multi-container will cause the user to lose confidence in the entire document. Always generate the actual deployable files (docker-compose.yml, Dockerfiles, nginx.conf, .env.example) alongside the prose spec and reference them by path. See `references/docker-compose-multi-container.md` for the canonical pattern.
