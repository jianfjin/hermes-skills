# Market Data Validation Pattern

How to check technology popularity with hard data before forming opinions in a council debate. Used in the 2026-05-15 SCAILED frontend debate reversal.

## Why This Exists

Council agents (Musk, Linus, Guido, etc.) reason from the brief they're given. If the brief omits external facts (client capabilities, market data, regional preferences), the entire debate operates on assumptions. This pattern provides the CTO with quick API queries to inject ground truth BEFORE the debate starts.

## API Recipes

### GitHub Stars & Forks

```bash
# Single repo
curl -s "https://api.github.com/repos/facebook/react" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'{d[\"full_name\"]}: {d[\"stargazers_count\"]}★, {d[\"forks_count\"]} forks')"

# Compare multiple
for repo in facebook/react vuejs/core sveltejs/svelte solidjs/solid; do
  curl -s "https://api.github.com/repos/$repo" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'{d[\"full_name\"]}: {d[\"stargazers_count\"]}★')"
done
```

### npm Weekly Downloads

```bash
# React
curl -s "https://api.npmjs.org/downloads/point/last-week/react" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'React: {d[\"downloads\"]:,}/week')"

# Compare multiple
for pkg in react vue next nuxt svelte; do
  curl -s "https://api.npmjs.org/downloads/point/last-week/$pkg" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'$pkg: {d[\"downloads\"]:,}/week')"
done
```

### Client GitHub Investigation

```bash
# Search client org for technology signals
curl -s "https://api.github.com/search/repositories?q=org:<orgname>+topic:react&per_page=5" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'React repos: {d[\"total_count\"]}')"

curl -s "https://api.github.com/search/repositories?q=org:<orgname>+topic:vue&per_page=5" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Vue repos: {d[\"total_count\"]}')"
```

### Client Documentation Search

```bash
# Search EU project proposals for tech stack mentions
grep -n -i "frontend\|front-end\|vue\|react\|typescript\|javascript\|tech.*stack\|code.*base" /path/to/proposal.txt
grep -n -i "existing.*system\|legacy\|repository\|technology.*stack" /path/to/proposal.txt
```

## Worked Example: SCAILED WP4 Frontend Debate Reversal (2026-05-15)

### What the council argued (based on brief only)

- "Vue 3 plain JS. React is overkill for a 4-screen wizard."
- "React reads like JavaScript having an identity crisis."
- "CHARITE biostatisticians can read Vue templates."

All 5 agents agreed: Vue 3, reject React.

### What the CTO discovered (post-debate validation)

1. **SCAILED proposal (4800+ lines)**: Zero mentions of CHARITE's tech stack, frontend preferences, or development team
2. **CHARITE public GitHub (bihealth)**: No React repos, no Vue repos — they're a research hospital, not a software company
3. **Market data**:
   - React: 245K ★, 132M weekly downloads
   - Vue: 54K ★, 12M weekly downloads
   - Ratio: React 10.7× larger
4. **Geographic context**: CHARITE is in Berlin. React dominates EU/German job market 5-8:1

### Reversal

React elevated from ✕ REJECTED to ✅ PRIMARY. Vue moved to ✅ VIABLE (Alternative). Final decision deferred to CHARITE/Epidata input via email (v3).

## Key Insight

The council is excellent at domain-internal reasoning (architecture, algorithms, ergonomics) but has zero visibility into external ground truth (market data, client capabilities, geography). The CTO must inject this data into the brief BEFORE the debate, or validate after and be prepared to reverse.

The best outcome is: council produces rigorous internal analysis, CTO overlays external market data, user (Emperor/client) makes the final call.
