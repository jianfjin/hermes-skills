# Docker Compose Topology Layout Heuristics

Patterns extracted from laying out the SCAILED WP4 8-container diagram
(viewBox 1100×620) with data-flow arrows, network boundaries, and a
vertical routing bus.  Use these as a starting point, not a straitjacket.

## ⚠️ CRITICAL: Data Flow vs HTTP Request Direction

Architecture diagrams show **data flow**, not HTTP request direction.
This is the #1 mistake:

```
WRONG (HTTP request direction):     Backend ──GET──→ Mock Service
RIGHT (data flow direction):        Mock Service ──data──→ Backend
```

Mock/Upstream services PROVIDE data. They are data SOURCES.
Arrows must point FROM upstream TO downstream (source → consumer).
The fact that the Backend initiates the HTTP GET does NOT mean the
arrow should point Backend→Mock.  Always draw the direction data travels.

In SVG with markers: when a line MUST be drawn in the "opposite"
direction (e.g. right→left because of fixed layout), `orient="auto"`
on the marker will rotate it to match the line direction — a standard
right-pointing marker on a right→left line points left.  No special
left-pointing marker needed.

### Convention by Flow Type

| Flow Type              | Arrow Direction            | Line Style      |
|------------------------|----------------------------|-----------------|
| Upstream → Backend     | Mock → Backend (data)      | Solid orange    |
| User → Proxy           | User → Traefik (request)   | Solid slate     |
| Proxy → Frontend       | Traefik → Frontend (files) | Solid cyan      |
| Backend → Database     | Backend → PG/Redis (write) | Dashed violet   |

## Grid Placement Rule

Arrange by data flow (left→right), NOT by who initiates the HTTP call:

```
[Upstream] → [Entry] → [Proxy] → [Backend] → [Data Stores]
 Mock-WPs     User      Traefik    FastAPI     PG / Redis
```

Or, when upstream is a column of services that must sit to the right
(due to horizontal space constraints), use right→left arrows with
auto-orient markers and a clear "Upstream" boundary label so the
reader knows data originates there:

```
[Entry] → [Proxy] → [Backend]   ←── [Upstream]
 User      Traefik    FastAPI    ←    Mock-WPs
                       ↓
                   [Data Stores]
                    PG / Redis
```

**Never** put upstream services in the same visual column as downstream
data stores (Postgres, Redis).  The eye will connect them vertically
and read it as "Postgres → Mock" — a false data flow.  Use separate
visual columns or a clear boundary box.

Vertical separation between rows: 140–170px (standard 60–85px component
height + 60–90px gap).  This leaves room for horizontal arrows with labels.

## Data Flow Arrow Routing

### Simple flows (adjacent columns, same row)
Standard horizontal line, label centered above:
```
<line x1="140" y1="300" x2="195" y2="300" .../>
<text x="167" y="292" ...>HTTPS</text>
```

### Cross-row flows (e.g. Traefik → Frontend, one row up)
Route with a single bend: go up first, then across.
```
<path d="M 265 265 L 265 195 L 395 195" .../>
```
Choose the bend point so the horizontal segment lands at the target's
mid-Y (target_y + target_h/2 — usually 10–15px below the component's
text center for a rectangular box).

### Many-to-many flows (e.g. 3 mock services → Backend)
Use a **vertical routing bus**: horizontal branches FROM each source to a
vertical spine, then one horizontal trunk FROM the spine TO the target.
```
<!-- branches: mocks → spine -->
<line x1="830" y1="147" x2="770" y2="147" .../>     <!-- wp2 → spine -->
<line x1="830" y1="300" x2="770" y2="300" .../>     <!-- wp3 → spine -->
<line x1="830" y1="448" x2="770" y2="448" .../>     <!-- wp8 → spine -->
<!-- spine -->
<line x1="770" y1="115" x2="770" y2="470" .../>
<!-- trunk: spine → backend -->
<line x1="770" y1="340" x2="570" y2="340" .../>
```

Place the spine at a clean X coordinate between the sources' right edge
and the target's left edge.  The spine must span the full Y range of all
sources.  Branch labels go on the horizontal segments.

When sources are to the RIGHT of the target (upstream on right),
lines go right→left.  Use `marker-end` with `orient="auto"` — the
arrowhead auto-rotates to point left.  No special marker needed.

## Network Boundaries

Draw boundaries BEFORE components (early in SVG) so they render behind.
Use the skill's existing two-dash styles:
- Region/cloud boundaries: `stroke-dasharray="8,4"` (amber)
- Security/network boundaries: `stroke-dasharray="5,3"` (cyan or emerald)
- Upstream boundaries: `stroke-dasharray="5,3"` (orange — `#fb923c`)

Overlapping boundaries (e.g. frontend network nested inside Docker
Compose boundary): draw the larger one first, then the smaller one.
Label them by placing text just inside the top edge:
```
<text x="rect_x + 12" y="rect_y + 18" ...>frontend network</text>
```

## Dotted vs Solid Arrows

- Solid arrows: HTTP/API traffic, static asset delivery, health checks,
  upstream data delivery
- Dashed arrows (`stroke-dasharray="6,3"`): SQL queries, cache operations,
  internal data-plane flows that aren't externally visible

## Component Dimensions (starting points)

| Role           | Width  | Height | When to adjust               |
|----------------|--------|--------|------------------------------|
| User/External  | 100–110| 50–60  | Single label, rarely need more |
| Proxy/Infra    | 120–130| 60–65  | Add sub-labels for TLS/rate-limit |
| Frontend       | 150–170| 80–85  | React/Vue stack, port, domain |
| Backend        | 150–170| 80–85  | Framework, port, async note  |
| Database (PG)  | 140–160| 75–82  | Engine + extension, port, vol|
| Cache (Redis)  | 140–160| 70–75  | Version, use-case, port, vol |
| Mock/Upstream  | 150–170| 75–80  | Library, port, data descriptor|

## Counting When Adding New Containers

Each new container adds ~110px of horizontal width or ~90px of vertical
height.  For the SCAILED diagram: 3 new mock containers fit in a
right-side column, increasing viewBox width from ~900 to 1150 and
height from ~480 to 620.

## Legend Placement

Place the legend OUTSIDE all boundaries (both the Docker Compose
boundary and any network boundaries).  Calculate the lowest Y of all
boundary rects and place the legend at least 20px below it.  If space
is tight on the right, use a two-column legend layout.

Label upstream arrows in the legend as "Upstream data →" (not "API Call")
to reinforce the data-flow convention.
