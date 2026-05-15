---
name: inner-circle-debate
description: Multi-profile inner circle debate system — spawn up to nine AI personas (CTO/CVO/CSA/Architect/Engineer/CPO/CLA/CSO/CIO) with different models for structured decision-making, code audits, and cross-review workflows.
version: 1.0.0
---

# Inner Circle Debate System

A multi-profile debate workflow where six AI personas — each with its own Hermes profile and model — discuss major decisions in parallel before a synthesized recommendation reaches the user.

## Concept

议会已扩编至9席（原6席 + 2026-05-13新增3席）：

```
┌──────────┬──────────────────────────┬────────────────────────────────┐
│ 席位     │ 身份                     │ 模型                           │
├──────────┼──────────────────────────┼────────────────────────────────┤
│ Feng Ge  │ CTO / 管理Agent          │ deepseek-v4-pro (主session)   │
│ Elon     │ CVO / 第一性原理         │ kimi-k2.6                      │
│ Xuefeng  │ CSA / 现实主义审计       │ deepseek-v4-flash              │
│ Linus    │ 首席架构师/内核审查      │ deepseek-v4-pro                │
│ Xiaolong │ 高级工程师/应用架构      │ deepseek-v4-pro                │
│ Jobs     │ CPO / 产品设计/PM        │ kimi-k2.6                      │
│ Guido    │ CLA / 语言与API设计      │ kimi-k2.6                      │
│ Dijkstra │ CSO / 算法正确性与形式化  │ kimi-k2.6                      │
│ Jensen   │ CIO / 硬件策略与算力     │ deepseek-v4-flash              │
└──────────┴──────────────────────────┴────────────────────────────────┘
```

## Roles & Responsibilities

| Seat | Role | Assignments |
|------|------|-------------|
| Feng Ge | CTO / Management | Orchestration, final synthesis, reporting to user |
| Elon Musk | CVO | First-principles deconstruction, physics-level analysis |
| Zhang Xuefeng | CSA | Realist cost-benefit audit, trap identification |
| Linus Torvalds | Chief Architect | System architecture, kernel-level code, code review |
| Zhang Xiaolong | Sr. Engineer | Application architecture, backend coding, "subtraction" |
| Steve Jobs | CPO/PM | Product design, UX, project management, business analysis |
| Guido van Rossum | CLA | API design, language readability, Pythonic standards, type systems |
| Edsger Dijkstra | CSO | Algorithmic correctness, formal verification, complexity analysis, concurrency |
| Jensen Huang | CIO | Hardware strategy, compute planning, GPU/infra optimization, deployment scaling |

Feng Ge assigns work based on expertise, moderates debates, and synthesizes all views into a final recommendation.

## Council Language Split

Five seats now operate in English-native SOUL.md (updated 2026-05-14):

| Language | Seats |
|----------|-------|
| **English** | Musk (CVO), Jobs (CPO), Linus (Arch), Guido (CLA), Dijkstra (CSO) |
| **Chinese** | Feng Ge (CTO), Zhang Xuefeng (CSA), Zhang Xiaolong (Eng), Jensen (CIO) |

When launching debate agents, use the appropriate language for each seat. English seats receive English prompts; Chinese seats receive Chinese prompts. Mixed-language debates are normal — the CTO synthesizes across both.

## Focused Debates (Not All 9 Seats)

For domain-specific questions, select only the relevant subset:

| Debate Type | Seats | When |
|-------------|-------|------|
| **Architecture** | Musk + Linus + Guido + Dijkstra + Xiaolong | Technology evaluation, stack decisions |
| **Product** | Jobs + Musk + Xuefeng | UX, feature prioritization, market fit |
| **Audit** | Xuefeng + Linus + Guido + Dijkstra | Contract review, technical debt, risk assessment |
| **External Eval** | Musk + Dijkstra + Guido + Linus + Xuefeng | Evaluating third-party frameworks/patterns (e.g., Palantir Ontology) |
| **Role Planning** | Xuefeng + Xiaolong + Jobs | Team structure, hiring, role assignment |

The CTO pre-digests inputs before launching the debate. Each agent should receive a focused question relevant to their seat, not the full technical brief. See `references/ontology-debate-findings.md` for an example of a focused external-evaluation debate.

**Related skills**: `ontology-patterns` — records the 4 patterns (Action Writeback, YAML→Pydantic codegen, Protocol polymorphism, FDE Lite) that emerged from the 2026-05-15 ontology debate. When the council evaluates a third-party framework and decides to adopt a subset, the resulting patterns should be saved to that skill.

## Setup (one-time)

### 1. Create profiles

```bash
# Original 6
hermes profile create musk --clone-from default
hermes profile create xuefeng --clone-from default
hermes profile create linus --clone-from default
hermes profile create xiaolong --clone-from default
hermes profile create steve --clone-from default

# 2026-05-13 expansion (3 new seats)
hermes profile create guido --clone-from default
hermes profile create dijkstra --clone-from default
hermes profile create jensen --clone-from default
```

### 2. Configure models

```bash
# Elon Musk — kimi-k2.6
musk config set model.default kimi-k2.6
musk config set model.provider kimi-coding-cn
musk config set model.context_length 65536
musk config set auxiliary.compression.context_length 65536

# Zhang Xuefeng — deepseek-v4-flash
xuefeng config set model.default deepseek-v4-flash
xuefeng config set model.provider deepseek

# Linus Torvalds — deepseek-v4-pro
linus config set model.default deepseek-v4-pro
linus config set model.provider deepseek

# Zhang Xiaolong — deepseek-v4-pro
xiaolong config set model.default deepseek-v4-pro
xiaolong config set model.provider deepseek

# Steve Jobs — kimi-k2.6
steve config set model.default kimi-k2.6
steve config set model.provider kimi-coding-cn
steve config set model.context_length 65536
steve config set auxiliary.compression.context_length 65536

# Guido van Rossum — kimi-k2.6
guido config set model.default kimi-k2.6
guido config set model.provider kimi-coding-cn
guido config set model.context_length 65536
guido config set auxiliary.compression.context_length 65536

# Edsger Dijkstra — kimi-k2.6
dijkstra config set model.default kimi-k2.6
dijkstra config set model.provider kimi-coding-cn
dijkstra config set model.context_length 65536
dijkstra config set auxiliary.compression.context_length 65536

# Jensen Huang — deepseek-v4-flash
jensen config set model.default deepseek-v4-flash
jensen config set model.provider deepseek
```

### 3. Customize personas (mandatory for cloned profiles)

**Important:** `--clone-from` copies SOUL.md as an empty template — the source profile's persona is NOT inherited. Every cloned profile needs its SOUL.md written before use.

Edit `~/.hermes/profiles/<name>/SOUL.md` with role-specific personality instructions. Without this, the agent speaks in the default Hermes tone with no persona.

**Language rule**: Non-Chinese seats (Musk, Jobs, Linus, Guido, Dijkstra, Jensen) MUST have English-only SOUL.md files. Chinese-language SOUL.md produces stilted, awkward output for these Western personas. Chinese seats (峰哥, 张雪峰, 张小龙) use Chinese SOUL.md. This is a first-class style requirement — the user explicitly prefers English for native-English council members.

### 4. Deploy the launch script

Copy `inner-circle-debate.sh` to `~/.hermes/scripts/` and `chmod +x` it. The script:
- Takes a debate topic as single argument
- Spawns both profiles in parallel
- Saves output to `/tmp/inner-circle-debate-<timestamp>/`
- Prints both positions

## Audit-Execute-Review Workflow

For code audits and multi-phase technical work, a proven 9-member workflow exists:
audit (selected seats in parallel) → synthesize (CTO) → execute fixes → re-audit → apply to all docs.

Full cycle demonstrated 2026-05-13 to 2026-05-14 for SCAILED WP4:

1. **Initial debate** (9 seats, day 1) → resolution + expanded analysis + email draft
2. **Re-audit** (6 seats, day 2) — Xuefeng, Musk, Jobs, Linus, Guido, Dijkstra re-examine all docs
3. **CTO synthesis** — compile audit findings into priority matrix (17 risks, 3 tiers)
4. **Apply to ALL documents** — resolution, expanded analysis, email, 3 HTML files. Use the audit risk matrix as a checklist; every finding must trace to a concrete change in every affected document.
5. **Commit with audit trail** — each revision gets a commit message referencing audit documents

Key principle: **Audit findings are not advisory. They are a punchlist.** After audit, every document that the audit touched must be reopened and patched. The CTO's job is to ensure zero findings are dropped between audit and execution.

Full details in `references/audit-execute-review-workflow.md`.

## Audit-Revision Workflow (Post-Council Document Update)

When a council debate produces documents (resolution, expanded analysis, emails, HTML reports)
and a follow-up audit identifies corrections, apply fixes systematically:

1. **Collect audit findings**: Each auditor produces a structured report (risks, severity, recommendations)
2. **CTO synthesizes**: Create a master audit report with risk matrix, priority tiers, and action checklist
3. **Apply fixes to all affected documents**: Resolution → expanded analysis → email → HTML reports.
   Never fix only the "main" document — downstream artifacts (emails, HTML) must stay in sync.
4. **Track what changed**: The resolution header should note audit date and scope. Each document's
   changes should be traceable to specific audit findings (risk IDs).
5. **Commit atomically**: One commit per audit revision cycle, with a commit message listing
   all documents changed and the audit sources.

Pitfall: It's tempting to only fix the resolution and call it done. But the email the client
reads and the HTML the team opens in a browser must reflect the corrected state. Out-of-sync
artifacts erode trust.

### Pattern A: One-shot debate (shell)

```bash
~/.hermes/scripts/inner-circle-debate.sh "Should Paperclip adopt GraphRAG over LLM-Wiki?"
```

Output goes to `/tmp/inner-circle-debate-<ts>/musk.txt` and `xuefeng.txt`.

### Pattern B: From within Hermes session (CTO orchestration)

Feng Ge spawns both profiles via `terminal(background=True, notify_on_complete=True)`:

```python
# Musk — first-principles analysis
terminal(
    command="musk chat -q 'Topic: X. Give your first-principles analysis.'",
    background=True,
    notify_on_complete=True
)

# Xuefeng — realist audit
terminal(
    command="xuefeng chat -q 'Topic: X. Give your cost-benefit realist audit.'",
    background=True,
    notify_on_complete=True
)
```

After both complete and notify, Feng Ge reads results and synthesizes for the user.

### Pattern D: Parallel 9-seat launch (CTO orchestration from Hermes session)

For full-council debates, launch all non-CTO seats as background processes, then poll and synthesize. This is the proven pattern from the 2026-05-13 SCAILED WP4 debate:

```python
# Phase 1: Launch all 8 non-CTO seats in parallel
terminal(command="musk chat -q '$(cat /tmp/brief.txt)\n\n[role prompt]'", background=True, notify_on_complete=True)
terminal(command="xuefeng chat -q '$(cat /tmp/brief.txt)\n\n[role prompt]'", background=True, notify_on_complete=True)
# ... repeat for guido, dijkstra, jensen, steve, linus, xiaolong

# Phase 2: Poll for status until all exit
process(action="poll", session_id="proc_xxx")

# Phase 3: Wait for slowest agents (kimi-k2.6 takes longest)
process(action="wait", session_id="proc_xxx", timeout=120)

# Phase 4: Extract full logs for archiving
process(action="log", session_id="proc_xxx", limit=500)

# Phase 5: CTO synthesizes all outputs into final report
```

**Key timing observations:**
- deepseek-v4-pro: ~40s-1m40s (Linus, Xiaolong most verbose)
- deepseek-v4-flash: ~34-40s (Jensen fastest)
- kimi-k2.6: ~42-58s (Musk, Guido, Dijkstra; Jobs ~36s)

**Sequence matters:** Launch deepseek models LAST (they finish first — they'll have results ready by the time you finish typing). Launch kimi-k2.6 models FIRST (they're the bottleneck).

### Council expansion workflow (add new seats)

When adding new council members, follow this checklist:

1. **Create profile**: `hermes profile create <name> --clone-from default`
2. **Configure model**: `<name> config set model.default <model>` + provider + context_length (65536 for kimi-k2.6)
3. **Remove stale base_url**: Edit config.yaml, delete the `base_url: https://api.deepseek.com/v1` line left from --clone-from
4. **Write SOUL.md**: Rich persona with identity, philosophy, role, communication style, quotes. English for non-Chinese members (Musk, Jobs, Linus, Guido, Dijkstra, Jensen). Chinese for Chinese members (Xuefeng, Xiaolong).
5. **Smoke test**: `<name> chat -q "Who are you? One sentence."`
6. **Update skill**: Patch the roster table, roles table, setup section, debate modes
7. **Update memory**: Add to the 9-seat roster entry
8. **Backup SOUL.md**: Copy to `~/projects/<project>/council_profiles/<name>_SOUL.md` for version control

### Pattern D: Full 9-member debate from within Hermes (2026-05-13, battle-tested)

For complex multi-stakeholder analysis (project proposals, architecture decisions, risk assessments), run all 8 non-CTO seats in parallel with a shared brief file. A complete real-world example with archived outputs and HTML artifacts is at `references/scailed-wp4-debate-example.md`.

**Step 1: Write the debate brief.** Structure it as a self-contained document that each agent can reason from without re-fetching external sources. See `references/debate-brief-template.md` for the template and anti-patterns. The brief should be pre-digested by the CTO — no raw URLs, no external references that would trigger browser/API calls. Save to `/tmp/<topic>_brief.txt`.

**Step 2: Launch all agents in parallel.** Each agent gets the brief + a role-specific question.

Do NOT inline the combined prompt directly in the terminal command — embedded quotes (especially Chinese quotation marks 「」「」 or smart quotes) will cause `bash: unexpected EOF` failures. Instead, **write each role's combined prompt to a separate file first**, then feed it to the profile:

```python
# Write combined prompt files via execute_code or write_file
# Brief is pre-written at /tmp/<topic>_brief.txt
# For each role, concatenate brief + role question into /tmp/audit_<role>.txt
# Avoid Chinese quotation marks in the prompt files — use plain text alternatives
```

```bash
# Then launch each agent:
terminal(command="<profile> chat -q \"$(cat /tmp/audit_<role>.txt)\"",
         background=True, notify_on_complete=True, timeout=600)
```

Launch all 8 non-CTO profiles. Observed completion times:
- deepseek-v4-flash (Xuefeng, Jensen): ~34-40s
- kimi-k2.6 (Musk, Guido, Dijkstra, Jobs): ~40-100s
- deepseek-v4-pro (Linus, Xiaolong): ~60-100s

**Step 3: Poll and wait.** Use `process(action='poll', session_id=...)` to check progress, then `process(action='wait', ...)` when output appears. The `notify_on_complete` flag sends a notification to the CTO's session.

**Step 4: Synthesize.** Feng Ge reads all outputs and produces a structured CTO report covering: key consensus, architecture, tech stack, sub-project breakdown, risk matrix, dependencies, and strategic ruling. The report should NOT just quote each member — it should integrate, reconcile conflicts, and add the management layer that none of the specialists provide.

**Critical:** Never include raw URLs or external references in the brief. The CTO pre-digests all source materials. Each agent's prompt must include an explicit role and output format instruction (e.g., `输出格式：[Musk/CVO] 分析...`). Without format instructions, agents may produce unlabeled or inconsistent output.

### Retrieving full agent outputs after completion

After agents complete, use `process(action='log', session_id=..., limit=500)` to retrieve the full output for archiving and synthesis. The `poll` and `wait` responses only show a truncated `output_preview` (last ~1KB). `log` returns the complete session transcript including the agent's entire response.

### `process(action='wait', ...)` timeout clamped to 60s

Requested wait timeouts (e.g., `timeout=120`) are clamped by the Hermes process infrastructure to a maximum of 60 seconds. If an agent is still running at the 60s clamp, re-issue `process(action='poll', ...)` to check status, then `process(action='wait', ...)` again. Deepseek-v4-pro agents (Linus, Xiaolong) may need 2 rounds of wait.

### Audit-Revise-Cascade (Step 6 — when debate outputs need hardening) (2026-05-14)

**Problem:** A full council debate produces a comprehensive synthesis, but the first-pass output inevitably has blind spots — over-aggressive wording in client-facing docs, missing technical edge cases, legal compliance gaps, project-management risks. The 9-seat debate catches the big picture but misses implementation-level detail.

**Solution:** Run a second, smaller **audit session** (3-6 seats, focused on review, not generation) against the debate's output documents. Then cascade every finding across ALL output artifacts. A 6-seat audit of the SCAILED WP4 debate found 17 risks (7 critical) in the original output — IP law violations, performance-critical architecture flaws, cash-flow gaps, and politically damaging wording.

**Pattern:**

1. **Debate → Document.** Full council produces: resolution, expanded analysis, email draft, HTML reports.
2. **File the outputs.** Save all documents to a project directory with structured naming (e.g., `council_debate_YYYYMMDD/00_resolution.md`, `01-08_speeches.txt`, `09_expanded_analysis.md`).
3. **Audit session.** Select 3-6 seats based on what needs hardening:
   - **Client-facing audit** (wording, contract, political risk): Xuefeng + Jobs + Musk + Guido
   - **Technical architecture audit** (performance, schema, tooling): Linus + Dijkstra + Guido
   - **Full audit** (all dimensions): Xuefeng + Musk + Jobs + Linus + Guido + Dijkstra
4. **Audit brief structure:** Point each auditor at the SPECIFIC documents to review. Ask each for: what's wrong, what's missing, what's politically dangerous, what's the fix. Give explicit output format and one assigned dimension per auditor.
5. **CTO synthesizes audit findings** into a single risk matrix with priorities and action items.
6. **Cascade fixes across ALL output documents.** This is the critical step. Every finding must be reflected in every document that touches that domain:
   - IP fix → resolution + expanded analysis + email + HTML spec
   - Payment split → resolution + expanded analysis + email + HTML plan
   - Wording fix → resolution + email + HTML report
   - Graph engine fix → resolution + expanded analysis + HTML spec + HTML plan
7. **Commit all** and push.

**Key insight:** The first debate catches the vision. The audit catches the execution. Both are needed. The cascade step is where most projects drop the ball — they fix the resolution but forget the email, or fix the email but not the HTML. Systematic document inventory prevents this.

**Document inventory to check during cascade:**
- `00_council_resolution.md` (the master record)
- `09_expanded_analysis.md` (technical details)
- `email_to_<client>_v<N>.md` (client-facing)
- `<name>-report.html` (synthesis)
- `<name>-spec.html` (architecture)
- `<name>-plan.html` (implementation plan)

See `references/scailed-wp4-audit-cascade-example.md` for the complete worked example with all 17 findings, the cascade matrix, and before/after diffs.

After the CTO synthesis, optional Step 5: convert the debate output into a self-contained HTML report using the `html-report` skill (Type C: Debate Synthesis pattern). This produces an interactive document with position cards, consensus box, SVG diagrams, and action items — suitable for sharing with stakeholders. Load `skill_view(name='html-report')` for the CSS design system and layout patterns. Also use `html-spec` for technical architecture documents and `html-plan` for implementation timelines derived from the debate.

## The Debate Script

The launch script is at `~/.hermes/scripts/inner-circle-debate.sh` and also bundled at `scripts/inner-circle-debate.sh` in this skill.

Supports three modes:
- `full` — all 6 seats (default)
- `tech` — Musk + Linus + Xiaolong (architecture & coding focus)
- `biz` — Musk + Jobs + Xuefeng (strategy & business focus)

Run directly or from within a Hermes session via `terminal(background=True)`.

## Model Reassignment

To change which model powers a seat:

```bash
# Example: swap Musk to a new model
musk config set model.default <new-model>
musk config set model.provider <new-provider>
```

Or add a new seat entirely:

```bash
hermes profile create <name> --clone-from default
<name> config set model.default <model>
<name> config set model.provider <provider>
```

## Pitfalls

### kimi-k2.6 extreme latency on formal-methods or deep-research prompts (2026-05-15)

kimi-k2.6 agents (Musk, Guido, Dijkstra, Jobs) are generally ~40-100s. But on prompts requiring formal mathematical analysis, tool-calling (search_files, grep, terminal probes), or deep reasoning, latency spikes to **3-6 minutes**. Observed: Dijkstra took 6m1s with 8 tool calls for an ontology formal-methods analysis. Musk took 3m22s for a first-principles evaluation.

**Mitigation**: 
- Give kimi-k2.6 seats focused, self-contained prompts that don't require tool use. Pre-digest any research the CTO can do (e.g., fetch Palantir docs, extract key concepts, put them in the brief).
- Launch kimi-k2.6 agents FIRST. Their completion time dominates the debate. deepseek-v4-pro/flash can wait.
- If a kimi-k2.6 agent hasn't produced output by 120s, poll and extend the wait. Don't assume failure — they're just slow.
- For time-critical debates, consider substituting deepseek-v4-pro for kimi-k2.6 seats if formal methods aren't the core of the question.
- The `process(action='wait', timeout=...)` is clamped to 60s. Re-issue waits for kimi agents.

### Debate prompt too long → initialization timeouts

Complex multi-topic debates with 3+ technical candidates and full background context can hit 2000+ words. Each agent loads skills, searches memory, and may try browser/API verification independently — 60s+ initialization before any output. On slow models (kimi-k2.6: 32K context), this is worse.

**Mitigation:** As CTO, pre-digest inputs before launching the debate. The debate topic should be a focused question with essential facts only, not a full technical brief. Each agent should NOT need to re-verify the same inputs independently. Provide the brief inline; let them reason from it.

**What to trim:** repo URLs (agents can't browse them anyway), full architecture descriptions they can load from skills, benchmark numbers they won't re-verify. What to keep: the core decision question, one-sentence per-candidate summaries, and Paperclip's current state.

### Agents independently re-verify inputs (browser/API loop trap)

Agents given a debate topic with external references (GitHub repos, URLs) will try to independently verify them — spawning browser sessions, curl calls, GitHub API queries. This wastes 2-3 minutes per agent on redundant work that the CTO already did. Observed: Xiaolong spent 3 minutes on browser → curl → Python GitHub API calls and never produced analysis.

**Fix:** Never include raw URLs in debate prompts. Pre-digest the technical analysis into the topic itself. State "the CTO has already verified these facts" explicitly. If an agent needs data it doesn't have, it should state assumptions and reason from them, not fetch.

### CTO synthesis pattern: reconcile extremist positions

When the council splits into extreme positions (e.g., "install everything now" vs "install nothing ever"), the CTO's job is to find the integrable middle: take the lightweight surface integration from the radical position, marry it with the architectural purity of the conservative position, and add the shipping pragmatism of the product position. See `references/debate-synthesis-patterns.md`.

### kimi-k2.6 context window (32K < Hermes 64K minimum)

Models with context windows below 64K fail Hermes's startup check. kimi-k2.6 (32,768 tokens) needs explicit overrides in TWO places:

```bash
<profile> config set model.context_length 65536
<profile> config set auxiliary.compression.context_length 65536
```

The first bypasses the main model check; the second bypasses the auxiliary compression model check (which defaults to the same model). Without the second, the error shifts from "Model kimi-k2.6 has a context window of 32,768" to "Auxiliary compression model kimi-k2.6 has a context window of 32,768".

See `references/kimi-k2.6-quirks.md` for full error transcripts and the resolution path.

### base_url contamination from --clone-from

`hermes profile create --clone-from default` copies the source profile's `model.base_url`. If the source uses DeepSeek (`https://api.deepseek.com/v1`) but the new profile uses a different provider (e.g., kimi-coding-cn), the wrong endpoint causes HTTP 401 authentication failures. Fix: remove the stale `base_url` from the cloned profile's `model:` section, or set it explicitly to the correct provider endpoint.

```yaml
# In ~/.hermes/profiles/<name>/config.yaml, under model: — DELETE:
# base_url: https://api.deepseek.com/v1   ← stale from clone
```

Or via CLI: edit the profile's config.yaml and remove the `base_url` line.

### SOUL.md clones as empty template

`--clone-from` copies the SOUL.md template file (comment block only, no persona content), NOT the source profile's active persona. Every cloned profile needs its SOUL.md written from scratch. Write it before the first `chat` invocation — otherwise the agent speaks in the default Hermes tone with no persona.

### bash builtin name conflicts

Profile aliases that shadow bash builtins (e.g., `jobs`) won't work from the shell wrapper. Use `hermes profile rename <old> <new>` to fix, or invoke via `hermes --profile <name>` instead. Check for conflicts before naming: `type <name>` should return "not found".

### Shell quoting failures with inline multi-line prompts (2026-05-14)

When launching agents via `terminal(command="<profile> chat -q \"...\"", ...)` with multi-line prompts containing Chinese quotation marks (「」「」), smart quotes, or other special characters, the shell will fail with `bash: unexpected EOF while looking for matching '"'`. This happens even when using `$(cat /tmp/brief.txt)` if the brief itself contains these characters.

**Fix:** Write each agent's combined prompt (brief + role-specific question) to a separate file using `write_file` or `execute_code` before launching. Strip all problematic quote characters from the prompt files — use plain text alternatives (e.g., 「导航」becomes 导航, 「AI」becomes AI). Then use `$(cat /tmp/audit_<role>.txt)` in the terminal command. The file-based approach avoids shell interpolation of the prompt content entirely.

**Verified pattern (2026-05-14, 6-agent audit):**
1. Write the shared brief to `/tmp/<topic>_brief.txt` (already done in Step 1)
2. Use `execute_code` to read the brief, concatenate with each role's question, and write to `/tmp/audit_<role>.txt`
3. Launch: `terminal(command="<profile> chat -q \"$(cat /tmp/audit_<role>.txt)\"", background=True, notify_on_complete=True, timeout=600)`
### Architecture review without content review (2026-05-12)

The council debated three-layer architecture, TF-IDF tuning, pickle security, and path
resolution for the EHDS knowledge graph — all architectural/technical concerns. Nobody
asked "show me a random query result." The KG was a skeleton: 37 placeholder Index articles
(avg 680 chars), 8 Wiki entries, 12 uningested PDFs. When the user queried the deployed RAG,
it returned empty generic responses. The architecture review passed. The content review
never happened.

**Fix:** Every debate about a knowledge base, RAG system, or search product must include a
**Step 0: Content Check** before any architecture discussion:

1. Run 3-5 random queries against the deployed system
2. Verify results span multiple layers (Index + Wiki + KB)
3. Check source document count vs. extracted topic count
4. If Step 0 fails, the debate topic is "how do we ingest content?" — not architecture

The Linus/Xiaolong seats (architecture, engineering) must be paired with a content-first
check: Xian check, then technical. First-principles analysis of a broken product is wasted
analysis.

### Delegate_task timeout on large batch operations (2026-05-14)

A delegate_task translating 9 large documents (Chinese→English) timed out at 600s with
only 6 API calls completed. The subagent likely hit slow API responses and couldn't
complete the batch.

**Fix:** For batch operations >5 large files, break into smaller delegate_task calls
(3-4 files each) or use sequential write_file calls from the CTO session. For translations:
if the content is known to the CTO (from prior reading), writing English versions directly
is faster than delegating. Use delegate_task for *unfamiliar* content that needs reading
first; use direct write_file for content the CTO already knows.
