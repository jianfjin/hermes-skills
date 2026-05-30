# REQUEST vs DATA vs WRITE Arrow Convention

## When to use

Use three arrow types when a system has:
1. Upstream data SOURCES (mock services, external APIs)
2. A processing backend
3. Downstream data SINKS (databases, caches, response to client)

Without all three, the diagram shows only half the story — data appears to "flow in and disappear."

## SVG implementation

### Markers

```svg
<!-- REQUEST: gray, thin -->
<marker id="req" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#64748b"/>
</marker>

<!-- DATA (upstream): orange, bold -->
<marker id="data-orange" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
  <polygon points="0 0, 10 4, 0 8" fill="#fb923c"/>
</marker>

<!-- DATA (response): cyan, bold -->
<marker id="data-cyan" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
  <polygon points="0 0, 10 4, 0 8" fill="#22d3ee"/>
</marker>

<!-- WRITE: violet, dashed -->
<marker id="write" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#a78bfa"/>
</marker>
```

### Lines

```svg
<!-- REQUEST: thin gray, solid -->
<line x1="400" y1="300" x2="550" y2="300" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>

<!-- DATA: bold orange, solid (upstream→backend) -->
<line x1="800" y1="300" x2="570" y2="300" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>

<!-- DATA: bold cyan, solid (backend→client) -->
<line x1="400" y1="335" x2="200" y2="335" stroke="#22d3ee" stroke-width="2" marker-end="url(#data-cyan)"/>

<!-- WRITE: dashed violet -->
<line x1="570" y1="180" x2="640" y2="180" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#write)"/>
```

### Labels

```svg
<text x="470" y="293" fill="#64748b" font-size="7">[REQ] GET /data</text>
<text x="680" y="293" fill="#fb923c" font-size="7">[DATA] upstream</text>
<text x="300" y="348" fill="#22d3ee" font-size="6">[DATA] JSON</text>
<text x="600" y="173" fill="#a78bfa" font-size="7">[WRITE] SQL</text>
```

## Parallel bus pattern (bidirectional links)

When two components exchange REQUEST and DATA in opposite directions:

```svg
<!-- REQUEST bus (offset 15px) -->
<line x1="570" y1="353" x2="815" y2="353" stroke="#94a3b8" stroke-width="1.2" marker-end="url(#req)"/>
<line x1="815" y1="120" x2="815" y2="495" stroke="#94a3b8" stroke-width="1"/>

<!-- DATA bus (offset -15px from REQUEST) -->
<line x1="800" y1="375" x2="570" y2="375" stroke="#fb923c" stroke-width="2" marker-end="url(#data-orange)"/>
<line x1="800" y1="130" x2="800" y2="505" stroke="#fb923c" stroke-width="1.5"/>
```

This avoids the ambiguity of a single bidirectional arrow.

## Legend card

Always include a legend in the info cards below the SVG:

```html
<div class="card">
  <div class="card-header"><div class="card-dot slate"></div><h3>REQUEST (gray)</h3></div>
  <ul><li>• HTTP calls, left→right</li></ul>
</div>
<div class="card">
  <div class="card-header"><div class="card-dot orange"></div><h3>DATA (orange/cyan)</h3></div>
  <ul><li>• Upstream→backend, backend→client</li></ul>
</div>
<div class="card">
  <div class="card-header"><div class="card-dot violet"></div><h3>WRITE (violet)</h3></div>
  <ul><li>• DB writes, dashed</li></ul>
</div>
```
