# Agent-D Comparison Debate Pattern

2026-05-17: 8-seat council debate comparing Parliament's design against an
independent Agent-D proposal (docs/, 11 documents). This established a 
reusable pattern for evaluating external proposals.

## Pattern

1. **Read all external docs first** — CTO pre-digests before launching debate
2. **Identify concrete disagreements** — avoid "I like X vs Y", find specific 
   architectural/schema/budget conflicts
3. **Assign seats by domain** — Architecture seats evaluate tech choices, 
   Audit seat evaluates budget, Product seat evaluates scope
4. **Require data-driven answers** — "React has 10x npm downloads in EU" 
   beats "Vue is simpler for non-frontend developers"
5. **CTO fusion verdict** — absorb what's better, reject what's over-engineered,
   produce a combined resolution

## Pitfalls from this session

- **Council self-congratulation**: Agents produced dismissive one-liners 
  ("React reads like JavaScript having an identity crisis") without data.
  User called this out: "不要继续自嗨了". Fix: require data in every claim.
- **Assumptions without evidence**: Council assumed CHARITE would maintain 
  Vue code without checking CHARITE's actual tech stack. User: "你们调查一下".
  Fix: before debating external preferences, research what the external 
  party actually uses.
- **Cost blindness**: Agent-D proposed €260K-320K scope for a €145K budget.
  Xuefeng's cost audit was the most valuable output. Fix: always include a 
  cost estimate in architecture debates.

## Reference

The full comparison verdict is at:
`scailed_wp4/council_debate_20260513/architecture-spec.html` §02e
