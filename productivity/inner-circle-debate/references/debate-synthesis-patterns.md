# Debate Synthesis Patterns

Recurring patterns observed when synthesizing split-council debates into CTO recommendations.

## Pattern 1: Radical vs Conservative vs Pragmatic Split

**Observed:** May 2026 — Paperclip EHDS tech selection debate (Graphify / MemPalace / agentmemory)

**Positions:**
- Musk (CVO): "Install agentmemory NOW — Hermes-native, lowest migration friction"
- Linus (Chief Architect): "Install NOTHING — iii-engine is arch debt, 100 lines of Python solves it"
- Jobs (CPO): "Install NOTHING — ship existing architecture, add temporal versioning to Wiki"

**Synthesis formula:** "Lightweight surface integration, not deep binding"

Take the radical's preferred option but apply it ONLY at the surface/MCP/server layer — never as core architecture. This gives the velocity benefit without the architectural dependency.

**Specific resolution:** Install agentmemory MCP server (npx command, config change) as Hermes session memory enhancer. Do NOT depend on iii-engine for compliance logic. Do NOT introduce TypeScript into the core Python stack.

This satisfies Musk ("use the integration"), Linus ("no arch debt"), and Jobs ("ship existing + enhance, don't delay").

## Pattern 2: Three-candidate evaluation framework

When evaluating N external candidates against an existing architecture:

1. **Category check:** Does candidate X solve the SAME problem we have? (Most failures happen here — Graphify for code, MemPalace for conversations, neither for regulations)
2. **Concept extraction:** What DESIGN IDEA from candidate X is valuable even if the tool is wrong? (Graphify's confidence tagging, MemPalace's temporal KG, agentmemory's content-addressable dedup)
3. **Integration friction:** What's the COST of partial adoption? (MCP server = low, iii-engine binding = high)

## Pattern 3: When two debaters time out

If some seats produce no output (initialization timeout, browser loop trap), the CTO proceeds with the available positions. The missing seats are noted in the synthesis but do not block the decision. The debate is advisory, not quorum-based.
