---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
version: 1.0.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw]
---

# Architecture Diagram Skill

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG graphics. No external tools, no API keys, no rendering libraries — just write the HTML file and open it in a browser.

## Scope

**Best suited for:**
- Software system architecture (frontend / backend / database layers)
- Cloud infrastructure (VPC, regions, subnets, managed services)
- Microservice / service-mesh topology
- Database + API map, deployment diagrams
- Anything with a tech-infra subject that fits a dark, grid-backed aesthetic

**Look elsewhere first for:**
- Physics, chemistry, math, biology, or other scientific subjects
- Physical objects (vehicles, hardware, anatomy, cross-sections)
- Floor plans, narrative journeys, educational / textbook-style visuals
- Hand-drawn whiteboard sketches (consider `excalidraw`)
- Animated explainers (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none fits, this skill can also serve as a general SVG diagram fallback — the output will just carry the dark tech aesthetic described below.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system below
3. Save with `write_file` to a `.html` file (e.g. `~/architecture-diagram.html`)
4. User opens in any browser — works offline, no dependencies

### Output Location

Save diagrams to a user-specified path, or default to the current working directory:
```
./[project-name]-architecture.html
```

### Preview

After saving, suggest the user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **Mock / Upstream** | `rgba(251, 146, 60, 0.18)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### Typography & Background
- **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background:** Slate-950 (`#020617`) with a subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent arrows from showing through semi-transparent fills, use a **double-rect masking technique**:
1. Draw an opaque background rect (`#0f172a`)
2. Draw the semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render behind component boxes
- **Arrowheads:** Defined via SVG markers
- **Security Flows:** Use dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### REQUEST vs DATA Dual-Arrow Pattern (CRITICAL)

When diagramming systems with upstream data sources (mock services, APIs, databases serving data), **REQUEST arrows and DATA arrows are two different flows that MUST be visually distinct**:

| Arrow Type | Color | Stroke | Direction | Meaning |
|-----------|-------|--------|-----------|---------|
| **REQUEST** | Gray (`#94a3b8` or `#64748b`) | Thin (`1.2px`) | Left→Right | HTTP call (who initiates) |
| **DATA** | Orange (`#fb923c`) or Cyan (`#22d3ee`) | Thick (`2px`) | Right→Left | Data response (what flows) |
| **WRITE** | Violet (`#a78bfa`) | Dashed (`1.5px`, `6,3`) | Left→Right | Database write |

**The cardinal rule**: HTTP request direction ≠ data flow direction. A Backend making `GET /api/v1/stakeholders` to a Mock service is a REQUEST flowing left→right. The stakeholder data returning is a DATA flow right→left. Architecture diagrams must show BOTH — otherwise the reader sees data flowing only INTO mock services (which makes no sense since mock services are upstream data providers).

**Example — correct dual-arrow between Backend and Mock**:
```svg
<!-- REQUEST: Backend → Mock (thin gray, left→right) -->
<line x1="570" y1="340" x2="815" y2="340" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>
<text x="680" y="333" fill="#64748b" font-size="7">[REQ] aiohttp GET</text>

<!-- DATA: Mock → Backend (thick orange, right→left) -->
<line x1="875" y1="365" x2="570" y2="365" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>
<text x="720" y="378" fill="#fb923c" font-size="7">[DATA] stakeholders</text>
```

**Common pitfall**: Drawing a single arrow `Backend → Mock` with a label like "GET /stakeholders" and calling it done. This shows the HTTP call but NOT the data flow. The result: the diagram implies data is flowing INTO the mock service, which is backwards — mock services PROVIDE data, they don't consume it. Always draw the return DATA arrow going the opposite direction.

**Parallel bus pattern for multiple upstream sources**:
When multiple upstream services connect to the same consumer, use parallel vertical buses — one for REQUEST, one for DATA — offset by ~15px:
```
REQUEST bus at x=815 (Backend→Mock branches)
DATA bus    at x=800 (Mock→Backend branches)
```

This prevents visual confusion from arrows crossing. Both buses connect to the Backend via horizontal trunk lines, one above the other.

### REQUEST/DATA marker definitions

```svg
<!-- REQUEST marker (thin, gray) -->
<marker id="req" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#64748b"/>
</marker>

<!-- DATA marker (bold, orange) -->
<marker id="data-orange" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
  <polygon points="0 0, 10 4, 0 8" fill="#fb923c"/>
</marker>

<!-- WRITE marker (dashed, violet) -->
<marker id="write" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#a78bfa"/>
</marker>
```

Note: When drawing right→left DATA arrows, use `orient="auto"` — the marker auto-rotates 180° to point left. No need for separate left-pointing marker definitions.

### Complete round-trip

Every architecture diagram showing request-response flows MUST show the full cycle:
1. **Request chain** (gray, thin): Client → Proxy → Backend → Upstream/Mock
2. **Data return chain** (colored, thick): Upstream/Mock → Backend → Proxy → Client
3. **Write path** (violet, dashed): Backend → Database/Cache

Without the return chain, the diagram implies data goes in and never comes out — a system with no output. Add data return arrows even if they partially overlap request paths. Offset them by 10-20px so both are visible.

After drawing, verify you can trace: Client ─REQ→ Backend ─REQ→ Upstream ─DATA→ Backend ─DATA→ Client. If any segment is missing, the diagram is incomplete.

### Legend

Always include a legend that distinguishes the three arrow types:

```svg
<line x1="x" y1="y" x2="x+30" y2="y" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>
<text>REQUEST (HTTP call)</text>

<line x1="x" y1="y+16" x2="x+30" y2="y+16" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>
<text>DATA (upstream → downstream)</text>

<line x1="x" y1="y+32" x2="x+30" y2="y+32" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#write)"/>
<text>WRITE (DB / Cache)</text>
```

### Upstream/downstream visual separation

Never place upstream services (mocks) in the same visual column as downstream data stores (Postgres, Redis). The eye connects vertically-aligned boxes, creating a false data flow like "Postgres → Mock". Use separate visual columns or explicit boundary boxes (e.g. `<rect>` with dashed orange stroke labeled "Upstream").

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must be placed *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must be placed outside all boundary boxes. Calculate the lowest Y-coordinate of all boundaries and place the legend at least 20px below it.

## Document Structure

The generated HTML file follows a four-part layout:
1. **Header:** Title with a pulsing dot indicator and subtitle
2. **Main SVG:** The diagram contained within a rounded border card
3. **Summary Cards:** A grid of three cards below the diagram for high-level details
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Template Reference

Load the full HTML template for the exact structure, CSS, and SVG component examples:

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

The template contains working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and the legend — use it as your structural reference when generating diagrams.

### Layout Heuristics

For complex Docker Compose / multi-container topologies with 8+ services, data-flow arrows, and network boundaries, consult the layout heuristics reference before laying out coordinates:

```
skill_view(name="architecture-diagram", file_path="references/docker-compose-layout-heuristics.md")
```

Covers: grid placement by layer, arrow routing (simple/cross-row/vertical-bus), network boundary layering, dotted-vs-solid conventions, component dimension starting points, and legend placement rules.

## Arrow Semantics: REQUEST vs DATA vs WRITE

The most common error in architecture diagrams: drawing HTTP request direction as if it were data flow direction. They are not the same.

| Arrow type | Direction | Meaning | Visual |
|-----------|-----------|---------|--------|
| REQUEST | Client → Server | Who initiates the HTTP call | Thin, gray/slate |
| DATA | Upstream → Downstream | Where the information flows | Thick, colored (orange/cyan) |
| WRITE | Backend → Database | Persistence operations | Dashed, violet |

**Example — Mock upstream services**:
```
REQUEST:  Backend ──[thin gray]──→ wp2-mock     (Backend sends GET)
DATA:     wp2-mock ──[thick orange]──→ Backend  (Mock returns data)
WRITE:    Backend ──[dashed violet]──→ PostgreSQL
```

**Pitfall**: If you draw only REQUEST arrows, the diagram shows data "flowing into" mock services and never coming out. The system looks like it only receives data and never returns it. Always show the complete round-trip: client → backend → upstream (request chain) AND upstream → backend → client (data chain).

**When to use dual-line pattern**: Every architecture diagram with upstream/downstream services needs REQUEST + DATA arrows running in opposite directions along the same path. Offset them vertically (one above, one below a shared bus line) and use clear `[REQ]` / `[DATA]` labels.

## Pitfalls

- **HTTP request direction ≠ data flow direction**. This is the #1 architecture-diagram error. An upstream service that the backend queries via HTTP GET is still an *upstream* data provider — data flows FROM upstream TO downstream, not the reverse. Arrows must show data direction (Mock → Backend), not HTTP call direction (Backend → Mock). If you need to show both, use separate arrow styles: thin gray lines for HTTP requests, thick colored lines for data flow.

- **Request-vs-Data pattern**: When a system has both HTTP requests and data returns, use three distinct arrow types:
  ```
  [REQ] gray thin solid   — HTTP request (who initiates the call)
  [DATA] orange bold      — upstream data flowing to processor
  [DATA] cyan bold        — response data flowing back to client
  [WRITE] violet dashed   — database/cache writes
  ```
  Add a legend explicitly labeling each type. A diagram that shows only the request direction looks like "data only flows in, nothing flows out" — always show the complete round-trip.

- **Upstream services need visual separation from storage**. When mock/upstream services and databases (Postgres, Redis) are both in the rightmost column, arrows can visually imply that databases feed into upstream services. Use a labeled boundary box (e.g., "Upstream (Mock WP Services)") and offset columns to prevent false connections. Full 3-arrow pattern (REQUEST/DATA/WRITE) with marker definitions in `references/request-data-write-arrow-pattern.html`.

### Arrow direction: data flow ≠ HTTP request direction

Architecture diagrams show **data flow**, not who initiates the HTTP call. Mock/Upstream services are data SOURCES — arrows must point FROM upstream TO downstream, never the reverse.

```
WRONG: Backend ──→ Mock      (HTTP request direction)
RIGHT: Mock ──→ Backend       (data flow direction)
```

When an upstream column sits to the RIGHT of the backend (due to horizontal space), draw right→left lines. SVG `orient="auto"` on markers auto-rotates arrowheads to match line direction — a standard right-pointing marker on a right→left line points left. No special left-pointing marker needed.

### REQUEST vs DATA vs WRITE — three arrow types for complete round-trip

When a system has both upstream data sources AND downstream data consumers, show the full round-trip with three visually distinct arrow types:

| Arrow | Style | Color | Stroke | Meaning |
|-------|-------|-------|--------|---------|
| REQUEST | Solid thin | `#94a3b8` (gray) | 1.2px | HTTP call direction (who initiates) |
| DATA | Solid bold | `#fb923c` (orange) / `#22d3ee` (cyan) | 2px | Actual data flow (upstream→downstream, response→client) |
| WRITE | Dashed | `#a78bfa` (violet) | 1.5px | Database writes (Backend→storage) |

**Marker definitions:** each type gets its own `<marker>` with appropriate fill color. REQUEST markers use smaller arrowheads (8×6); DATA markers use prominent arrowheads (10×8).

**Label convention:** prefix every arrow label with `[REQ]`, `[DATA]`, or `[WRITE]` so the reader instantly knows which type.

**Complete round-trip example (mock upstream → backend → client):**
```
[REQ] Client ──→ Traefik ──→ Backend ──→ Mock-Services    (HTTP calls)
[DATA] Mock-Services ──→ Backend ──→ Client                (upstream data, API response)
[WRITE] Backend - -→ PostgreSQL / Redis                    (persistence)
```

**Parallel buses for bidirectional links:** when two components exchange REQUEST and DATA in opposite directions (e.g. Backend↔Mock), draw two parallel vertical/horizontal lines — one for REQUEST, one for DATA — slightly offset (15-20px apart). This is clearer than a single bidirectional arrow.

Reference: `references/request-data-write-arrows.md`

### Upstream/downstream visual separation

Never place upstream services (mocks) in the same visual column as downstream data stores (Postgres, Redis). The eye connects vertically-aligned boxes, creating a false data flow like "Postgres → Mock". Use separate visual columns or explicit boundary boxes (e.g. `<rect>` with dashed orange stroke labeled "Upstream").
