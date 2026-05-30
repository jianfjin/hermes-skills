# Right→Left Arrow Technique for SVG Architecture Diagrams

## Problem

When drawing upstream → downstream data flow in a left-to-right layout, upstream services may sit to the RIGHT of the processor (due to horizontal space constraints). But data must flow FROM upstream (right) TO downstream (left). The standard right-pointing SVG marker (`points="0 0, 10 3.5, 0 7"`) points right — drawing a right→left line would leave the arrowhead pointing the wrong way.

## Solution: orient="auto" + right→left line

SVG's `orient="auto"` on `<marker>` rotates the marker to match the LINE direction. When you draw a line from X=855 (right) to X=740 (left), the line vector is LEFT. `orient="auto"` rotates the right-pointing marker 180°, and it now points LEFT.

```xml
<!-- Standard right-pointing marker -->
<marker id="ah-orange" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#fb923c"/>
</marker>

<!-- Line goes right→left, marker-end auto-rotates to point left -->
<line x1="855" y1="147" x2="740" y2="147" stroke="#fb923c" stroke-width="1.3" marker-end="url(#ah-orange)"/>
```

No need for a separate left-pointing marker definition. The SAME right-pointing marker works for both directions.

## Dual Bus Pattern (REQUEST + DATA on same path)

When showing both HTTP REQUEST (Backend→Mock) and DATA return (Mock→Backend) along the same horizontal corridor, use TWO parallel vertical buses:

```xml
<!-- REQUEST bus (gray, thin, offset RIGHT) -->
<line x1="815" y1="120" x2="815" y2="495" stroke="#94a3b8" stroke-width="1"/>
<!-- DATA bus (orange, bold, offset LEFT) -->
<line x1="800" y1="130" x2="800" y2="505" stroke="#fb923c" stroke-width="1.5"/>

<!-- REQUEST: Backend → bus → Mock (left→right) -->
<line x1="570" y1="353" x2="815" y2="353" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>
<line x1="815" y1="140" x2="875" y2="140" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>

<!-- DATA: Mock → bus → Backend (right→left, auto-orient handles arrow) -->
<line x1="875" y1="160" x2="800" y2="160" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>
<line x1="800" y1="375" x2="570" y2="375" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>
```

Offset the DATA branches slightly BELOW the REQUEST branches (e.g., y=140 vs y=160) so the two lines don't overlap.

## Pitfall: Postgres/Redis visual alignment with mocks

When upstream services (mocks) sit at x=855 and data stores (Postgres, Redis) sit at x=640 with a bus at x=740, the eye may connect them vertically: Postgres→(gap)→bus→Mock, creating a false "Postgres flows into Mocks" impression.

Fix: Add an explicit "Upstream" boundary box around mock services, and ensure Postgres/Redis are placed in a separate visual column with clear separation. The boundary's label ("Upstream (Mock WP Services)") breaks the false vertical connection.
