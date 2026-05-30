---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent."
version: 2.3.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 10+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## CLI Reference

### Global Flags

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

No subcommand defaults to `chat`.

### Chat

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Configuration

```
hermes setup [section]      Interactive wizard (model|terminal|gateway|tools|agent)
hermes model                Interactive model/provider picker
hermes config               View current config
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check for missing/outdated config
hermes config migrate       Update config with new options
hermes login [--provider P] OAuth login (nous, openai-codex)
hermes logout               Clear stored auth
hermes doctor [--fix]       Check dependencies and config
hermes status [--all]       Show component status
```

### Tools & Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill (ID can be a hub identifier OR a direct https://…/SKILL.md URL; pass --name to override when frontmatter has no name)
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Gateway (Messaging Platforms)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI connects via the API Server adapter.

Platform docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Profiles

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
```

### Cross-Machine Hermes Migration

To replicate a Hermes setup (profiles, skills, scripts, memory) to another machine:

**Step 1: Package essentials only.** Profiles contain large caches (skills/ copies, bin/, sessions/) that are auto-regenerated. Only `config.yaml` and `SOUL.md` per profile are needed:

```bash
tar czf /tmp/hermes-migration-$(date +%Y%m%d).tar.gz \
  -C ~ \
  .hermes/config.yaml \
  .hermes/profiles/*/config.yaml \
  .hermes/profiles/*/SOUL.md \
  .hermes/skills/ \
  .hermes/scripts/ \
  .hermes/memories/
```

A full 8-profile setup with skills compresses to ~3MB.

**Step 2: Transfer and unpack on new machine:**

```bash
scp user@old-vm:/tmp/hermes-migration-*.tar.gz ~/
tar xzf hermes-migration-*.tar.gz -C ~/
```

**Step 3: Re-create profiles.** The unpacked files go to the right directories, but Hermes needs profiles registered:

```bash
for p in musk xuefeng linus xiaolong steve guido dijkstra jensen; do
  hermes profile create $p --clone-from default
done
# The unpacked config.yaml and SOUL.md now override cloned defaults
```

**What NOT to migrate:** profiles/*/skills/ (auto-regenerated, 12MB+ each), profiles/*/bin/ (platform-specific), profiles/*/sessions/ (diverges naturally), API keys (reconfigure or use password manager).

### Two-Machine Sync Strategy

Treat skills and profiles as code:

1. **Skills repo:** `cd ~/.hermes/skills && git init && git push`. Sync via `git pull`.
2. **Profile SOUL.md:** Already versioned in project repo. Copy after changes.
3. **config.yaml:** Do NOT git (API keys). Manual sync or password-manager CLI.
4. **Auto-sync:** Optional cron: `cd ~/.hermes/skills && git pull --rebase`

### OAuth / Device-code auth

```bash
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

**Headless VM (no browser):** use `hermes auth add <provider> --no-browser`.
Opens device-code flow instead of local web server. See
`references/headless-vm-oauth.md` for the full workflow and PTY-capture
pitfalls.

### Other

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration (requires honcho plugin)
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---

## Slash Commands (In-Session)

Type these during an interactive chat session. New commands land fairly
often; if something below looks stale, run `/help` in-session for the
authoritative list or see the [live slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands).
The registry of record is `hermes_cli/commands.py` — every consumer
(autocomplete, Telegram menu, Slack mapping, `/help`) derives from it.

### Session Control
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/snapshot [sub]      Create or restore state snapshots of Hermes config/state (CLI)
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/steer <prompt>      Inject a message after the next tool call without interrupting
/agents (/tasks)     Show active agents and running tasks
/resume [name]       Resume a named session
/goal [text|sub]     Set a standing goal Hermes works on across turns until achieved
                     (subcommands: status, pause, resume, clear)
/redraw              Force a full UI repaint (CLI)
```

### Configuration
```
/config              Show config (CLI)
/model [name]        Show or change model
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/busy [sub]          Control what Enter does while Hermes is working (CLI)
                     (subcommands: queue, steer, interrupt, status)
/indicator [style]   Pick the TUI busy-indicator style (CLI)
                     (styles: kaomoji, emoji, unicode, ascii)
/footer [on|off]     Toggle gateway runtime-metadata footer on final replies
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Tools & Skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/reload-skills       Re-scan ~/.hermes/skills/ for added/removed skills
/reload              Reload .env variables into the running session (CLI)
/reload-mcp          Reload MCP servers
/cron                Manage cron jobs (CLI)
/curator [sub]       Background skill maintenance (status, run, pin, archive, …)
/kanban [sub]        Multi-profile collaboration board (tasks, links, comments)
/plugins             List plugins (CLI)
```

### Gateway
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/topic [sub]         Enable or inspect Telegram DM topic sessions (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Utility
```
/branch (/fork)      Branch the current session
/fast                Toggle priority/fast processing
/browser             Open CDP browser connection
/history             Show conversation history (CLI)
/save                Save conversation to file (CLI)
/copy [N]            Copy the last assistant response to clipboard (CLI)
/paste               Attach clipboard image (CLI)
/image               Attach local image file (CLI)
```

### Info
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/gquota              Show Google Gemini Code Assist quota usage (CLI)
/status              Session info (gateway)
/profile             Active profile info
/debug               Upload debug report (system info + logs) and get shareable links
```

### Exit
```
/quit (/exit, /q)    Exit CLI
```

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

### Config Sections

Edit with `hermes config edit` or `hermes config set section.key value`.

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `base_url`, `api_key`, `max_iterations` (50), `reasoning_effort` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Providers

20+ providers supported. Set via `hermes model` or `hermes setup`.

| Provider | Auth | Key env var |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes auth` |
| OpenAI Codex | OAuth | `hermes auth` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| Google Gemini | API key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| xAI / Grok | API key | `XAI_API_KEY` |
| Groq (LLM inference) | API key (gsk_ prefix) | `GROQ_API_KEY` | `base_url: https://api.groq.com/openai/v1` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| MiniMax CN | API key | `MINIMAX_CN_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | API key | `XIAOMI_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| AI Gateway (Vercel) | API key | `AI_GATEWAY_API_KEY` |
| OpenCode Zen | API key | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | API key | `OPENCODE_GO_API_KEY` |
| Qwen OAuth | OAuth | `hermes login --provider qwen-oauth` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Full provider docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

| Toolset | What it provides |
|---------|-----------------|
| `web` | Web search and content extraction |
| `search` | Web search only (subset of `web`) |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `vision` | Image analysis |
| `image_gen` | AI image generation |
| `video` | Video analysis and generation |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `messaging` | Cross-platform message sending |
| `todo` | In-session task planning and tracking |
| `kanban` | Multi-agent work-queue tools (gated to workers) |
| `debugging` | Extra introspection/debug tools (off by default) |
| `safe` | Minimal, low-risk toolset for locked-down sessions |
| `spotify` | Spotify playback and playlist control |
| `homeassistant` | Smart home control (off by default) |
| `discord` | Discord integration tools |
| `discord_admin` | Discord admin/moderation tools |
| `feishu_doc` | Feishu (Lark) document tools |
| `feishu_drive` | Feishu (Lark) drive tools |
| `yuanbao` | Yuanbao integration tools |
| `rl` | Reinforcement learning tools (off by default) |
| `moa` | Mixture of Agents (off by default) |

Full enumeration lives in `toolsets.py` as the `TOOLSETS` dict; `_HERMES_CORE_TOOLS` is the default bundle most platforms inherit from.

Tool changes take effect on `/reset` (new session). They do NOT apply mid-conversation to preserve prompt caching.

---

## Security & Privacy Toggles

Common "why is Hermes doing X to my output / tool calls / commands?" toggles — and the exact commands to change them. Most of these need a fresh session (`/reset` in chat, or start a new `hermes` invocation) because they're read once at startup.

### Secret redaction in tool output

Secret redaction is **off by default** — tool output (terminal stdout, `read_file`, web content, subagent summaries, etc.) passes through unmodified. If the user wants Hermes to auto-mask strings that look like API keys, tokens, and secrets before they enter the conversation context and logs:

```bash
hermes config set security.redact_secrets true       # enable globally
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

By default (`approvals.mode: manual`), Hermes prompts the user before running shell commands flagged as destructive (`rm -rf`, `git reset --hard`, etc.). The modes are:

- `manual` — always prompt (default)
- `smart` — use an auxiliary LLM to auto-approve low-risk commands, prompt on high-risk
- `off` — skip all approval prompts (equivalent to `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Per-invocation bypass without changing config:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Note: YOLO / `approvals.mode: off` does NOT turn off secret redaction. They are independent.

### Shell hooks allowlist

Some shell-hook integrations require explicit allowlisting before they fire. Managed via `~/.hermes/shell-hooks-allowlist.json` — prompted interactively the first time a hook wants to run.

### Disabling the web/browser/image-gen tools

To keep the model away from network or media tools entirely, open `hermes tools` and toggle per-platform. Takes effect on next session (`/reset`). See the Tools & Skills section above.

---

## Voice & Transcription

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key: `pip install faster-whisper`
2. **Groq Whisper** — free tier: set `GROQ_API_KEY`
3. **OpenAI Whisper** — paid: set `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — set `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\r` vs `\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry

### Multi-Profile Parallel Agents (Debate Pattern)

Run **different profiles with different models** in parallel to simulate a multi-agent debate. Each profile gets its own model/provider assignment, isolated sessions, and independent context:

```bash
# 1. Create profiles
hermes profile create musk --clone-from default
hermes profile create xuefeng --clone-from default

# 2. Assign models
musk config set model.default kimi-k2.6
musk config set model.provider kimi-coding-cn
xuefeng config set model.default deepseek-v4-flash
xuefeng config set model.provider deepseek

# 3. Launch in parallel (one-shot)
~/.hermes/scripts/inner-circle-debate.sh "debate topic"

# 4. Or from a parent Hermes session:
terminal(command="musk chat -q '...'", background=true, notify_on_complete=true)
terminal(command="xuefeng chat -q '...'", background=true, notify_on_complete=true)
```

Each profile gets a CLI wrapper at `~/.local/bin/<name>`. See `references/multi-profile-parallel-agents.md` for the full pattern, and `scripts/inner-circle-debate.sh` for the launcher script.

### Multi-Profile Implementation Delegation (Code Workflow)

For code writing and review workflows through persona profiles, use `hermes -p <profile> chat -q` with file-writing capabilities:

```bash
# Architecture review (returns text verdict)
terminal(command="hermes -p linus chat -q '...review this plan...' --quiet -t terminal,file", background=true)

# Python/Schema review (returns text verdict)
terminal(command="hermes -p guido chat -q '...review schema...' --quiet -t terminal,file", background=true)

# Code implementation (writes files via terminal tools)
terminal(command="hermes -p xiaolong chat -q '...write code...' --quiet -t terminal,file", background=true, timeout=900)
```

**Key differences from debate pattern:**
- Profiles write code files to disk via their `terminal` tool access
- `-t terminal,file` flags must be explicit to enable writing
- `timeout` must be set high (600-900s) for multi-file implementations
- Collect results via `process(..., action=wait|log)` after completion
- Use `notify_on_complete=true` to get notified when each profile finishes

**NSFW note:** deepseek-v4-pro/flash rejects explicit content at the provider level even when SOUL.md authorizes it. Use xAI Grok models for profiles that need to generate NSFW content. See `references/delegate-vs-profile-chat.md` for the full NSFW guardrail comparison table.

---

## Using Hermes as a Backend API Server

The Hermes Gateway API Server (port 8642 by default) exposes an **OpenAI-compatible `/v1/chat/completions`** endpoint. This lets you replace a custom RAG/LLM backend service with a direct call to Hermes — the frontend calls the Hermes API instead of your own Python server.

```bash
# Quick test
curl -s http://localhost:8642/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sekret" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hello"}]}'
```

Three architectural patterns are documented in `references/api-server-as-backend.md`:

| Pattern | Frontend Change | Backend Change | Best For |
|---------|:--------------:|:--------------:|----------|
| **A: Direct call** | ~12 lines | 0 | New projects, controlled frontend |
| **B: Thin proxy** | 0 | Rewrite backend | Existing backend contract |
| **C: Webhook** | Full rewrite | N/A | Async notifications only |

Key pitfalls covered in the reference: OpenAI response format vs custom schema, stateless session management (pass full history each time), missing sources/citations (instruct in system prompt or post-process), CORS config, and auth header format.

---

## Durable & Background Systems

Four systems run alongside the main conversation loop. Quick reference
here; full developer notes live in `AGENTS.md`, user-facing docs under
`website/docs/user-guide/features/`.

### Delegation (`delegate_task`)

Synchronous subagent spawn — the parent waits for the child's summary
before continuing its own loop. Isolated context + terminal session.

- **Single:** `delegate_task(goal, context, toolsets)`.
- **Batch:** `delegate_task(tasks=[{goal, ...}, ...])` runs children in
  parallel, capped by `delegation.max_concurrent_children` (default 3).
- **Roles:** `leaf` (default; cannot re-delegate) vs `orchestrator`
  (can spawn its own workers, bounded by `delegation.max_spawn_depth`).
- **Not durable.** If the parent is interrupted, the child is
  cancelled. For work that must outlive the turn, use `cronjob` or
  `terminal(background=True, notify_on_complete=True)`.

Config: `delegation.*` in `config.yaml`.

### Cron (scheduled jobs)

Durable scheduler — `cron/jobs.py` + `cron/scheduler.py`. Drive it via
the `cronjob` tool, the `hermes cron` CLI (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`), or the `/cron` slash command.

- **Schedules:** duration (`"30m"`, `"2h"`), "every" phrase
  (`"every monday 9am"`), 5-field cron (`"0 9 * * *"`), or ISO timestamp.
- **Per-job knobs:** `skills`, `model`/`provider` override, `script`
  (pre-run data collection; `no_agent=True` makes the script the whole
  job), `context_from` (chain job A's output into job B), `workdir`
  (run in a specific dir with its `AGENTS.md` / `CLAUDE.md` loaded),
  multi-platform delivery.
- **Invariants:** 3-minute hard interrupt per run, `.tick.lock` file
  prevents duplicate ticks across processes, cron sessions pass
  `skip_memory=True` by default, and cron deliveries are framed with a
  header/footer instead of being mirrored into the target gateway
  session (keeps role alternation intact).

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (skill lifecycle)

Background maintenance for agent-created skills. Tracks usage, marks
idle skills stale, archives stale ones, keeps a pre-run tar.gz backup
so nothing is lost.

- **CLI:** `hermes curator <verb>` — `status`, `run`, `pause`, `resume`,
  `pin`, `unpin`, `archive`, `restore`, `prune`, `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` mirrors the CLI.
- **Scope:** only touches skills with `created_by: "agent"` provenance.
  Bundled + hub-installed skills are off-limits. **Never deletes** —
  max destructive action is archive. Pinned skills are exempt from
  every auto-transition and every LLM review pass.
- **Telemetry:** sidecar at `~/.hermes/skills/.usage.json` holds
  per-skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Config: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (multi-agent work queue)

Durable SQLite board for multi-profile / multi-worker collaboration.
Users drive it via `hermes kanban <verb>`; dispatcher-spawned workers
see a focused `kanban_*` toolset gated by `HERMES_KANBAN_TASK` so the
schema footprint is zero outside worker processes.

- **CLI verbs (common):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Less common: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Worker toolset:** `kanban_show`, `kanban_complete`, `kanban_block`,
  `kanban_heartbeat`, `kanban_comment`, `kanban_create`, `kanban_link`.
- **Dispatcher** runs inside the gateway by default
  (`kanban.dispatch_in_gateway: true`) — reclaims stale claims,
  promotes ready tasks, atomically claims, spawns assigned profiles.
  Auto-blocks a task after ~5 consecutive spawn failures.
- **Isolation:** board is the hard boundary (workers get
  `HERMES_KANBAN_BOARD` pinned in env); tenant is a soft namespace
  within a board for workspace-path + memory-key isolation.

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban

---

## Windows-Specific Quirks

Hermes runs natively on Windows (PowerShell, cmd, Windows Terminal, git-bash
mintty, VS Code integrated terminal). Most of it just works, but a handful
of differences between Win32 and POSIX have bitten us — document new ones
here as you hit them so the next person (or the next session) doesn't
rediscover them from scratch.

### Input / Keybindings

**Alt+Enter doesn't insert a newline.** Windows Terminal intercepts Alt+Enter
at the terminal layer to toggle fullscreen — the keystroke never reaches
prompt_toolkit. Use **Ctrl+Enter** instead. Windows Terminal delivers
Ctrl+Enter as LF (`c-j`), distinct from plain Enter (`c-m` / CR), and the
CLI binds `c-j` to newline insertion on `win32` only (see
`_bind_prompt_submit_keys` + the Windows-only `c-j` binding in `cli.py`).
Side effect: the raw Ctrl+J keystroke also inserts a newline on Windows —
unavoidable, because Windows Terminal collapses Ctrl+Enter and Ctrl+J to
the same keycode at the Win32 console API layer. No conflicting binding
existed for Ctrl+J on Windows, so this is a harmless side effect.

mintty / git-bash behaves the same (fullscreen on Alt+Enter) unless you
disable Alt+Fn shortcuts in Options → Keys. Easier to just use Ctrl+Enter.

**Diagnosing keybindings.** Run `python scripts/keystroke_diagnostic.py`
(repo root) to see exactly how prompt_toolkit identifies each keystroke
in the current terminal. Answers questions like "does Shift+Enter come
through as a distinct key?" (almost never — most terminals collapse it
to plain Enter) or "what byte sequence is my terminal sending for
Ctrl+Enter?" This is how the Ctrl+Enter = c-j fact was established.

### Config / Files

**HTTP 400 "No models provided" on first run.** `config.yaml` was saved
with a UTF-8 BOM (common when Windows apps write it). Re-save as UTF-8
without BOM. `hermes config edit` writes without BOM; manual edits in
Notepad are the usual culprit.

### `execute_code` / Sandbox

**WinError 10106** ("The requested service provider could not be loaded
or initialized") from the sandbox child process — it can't create an
`AF_INET` socket, so the loopback-TCP RPC fallback fails before
`connect()`. Root cause is usually **not** a broken Winsock LSP; it's
Hermes's own env scrubber dropping `SYSTEMROOT` / `WINDIR` / `COMSPEC`
from the child env. Python's `socket` module needs `SYSTEMROOT` to locate
`mswsock.dll`. Fixed via the `_WINDOWS_ESSENTIAL_ENV_VARS` allowlist in
`tools/code_execution_tool.py`. If you still hit it, echo `os.environ`
inside an `execute_code` block to confirm `SYSTEMROOT` is set. Full
diagnostic recipe in `references/execute-code-sandbox-env-windows.md`.

### Testing / Contributing

**`scripts/run_tests.sh` doesn't work as-is on Windows** — it looks for
POSIX venv layouts (`.venv/bin/activate`). The Hermes-installed venv at
`venv/Scripts/` has no pip or pytest either (stripped for install size).
Workaround: install `pytest + pytest-xdist + pyyaml` into a system Python
3.11 user site, then invoke pytest directly with `PYTHONPATH` set:

```bash
"/c/Program Files/Python311/python" -m pip install --user pytest pytest-xdist pyyaml
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/foo/test_bar.py -v --tb=short -n 0
```

Use `-n 0`, not `-n 4` — `pyproject.toml`'s default `addopts` already
includes `-n`, and the wrapper's CI-parity guarantees don't apply off POSIX.

**POSIX-only tests need skip guards.** Common markers already in the codebase:
- Symlinks — elevated privileges on Windows
- `0o600` file modes — POSIX mode bits not enforced on NTFS by default
- `signal.SIGALRM` — Unix-only (see `tests/conftest.py::_enforce_test_timeout`)
- Winsock / Windows-specific regressions — `@pytest.mark.skipif(sys.platform != "win32", ...)`

Use the existing skip-pattern style (`sys.platform == "win32"` or
`sys.platform.startswith("win")`) to stay consistent with the rest of the
suite.

### Path / Filesystem

**Line endings.** Git may warn `LF will be replaced by CRLF the next time
Git touches it`. Cosmetic — the repo's `.gitattributes` normalizes. Don't
let editors auto-convert committed POSIX-newline files to CRLF.

**Forward slashes work almost everywhere.** `C:/Users/...` is accepted by
every Hermes tool and most Windows APIs. Prefer forward slashes in code
and logs — avoids shell-escaping backslashes in bash.

---

## Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues

#### OpenAI Codex / OAuth provider: `'NoneType' object is not iterable`

When using the `openai-codex` provider (OAuth device-code flow) with ANY model, the agent immediately crashes with:
```
Error: 'NoneType' object is not iterable
```
**DO NOT** assume the model name is wrong — it's an SDK-level bug that affects all models on this provider.

**Root cause:** OpenAI Python SDK (v2.32.0–2.38.0) has a bug in `openai/lib/_parsing/_responses.py`, function `parse_response()`, line 61. The Codex OAuth backend streams events with `"output": null` in the response. The SDK's code:
```python
for output in response.output:  # <-- crashes when response.output is None
```
Does not guard against `None`.

**Fix:** Patch the SDK in two locations:
```bash
# Location 1: user-site (used by standalone Python)
~/.local/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py

# Location 2: Hermes agent venv (used by `hermes` CLI)
~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py
```
Change line 61 from:
```python
    for output in response.output:
```
to:
```python
    for output in (response.output or []):
```

**Verification:** After patching, test with any profile:
```bash
hermes -p <profile> chat -q 'Hi' --model gpt-5.3-codex --provider openai-codex
```

**Caveat:** This patch is overwritten on `pip install --upgrade openai`. Re-apply after SDK upgrades.

See `references/codex-oauth-sdk-bug-debug.md` for the full diagnostic trace, reproduction script, and maintenance sed command.

**Additional Codex OAuth quirks discovered:**
- The Codex backend (`chatgpt.com/backend-api/codex`) **requires** `stream=True` — non-streaming calls return 400
- The `input` field must be a list (e.g. `[{"role": "user", "content": "..."}]`), not a string
- Available models are gated by ChatGPT account entitlements — not all models in DEFAULT_CODEX_MODELS (`hermes_cli/codex_models.py`) are available to every account
- The OAuth credential is stored in `~/.hermes/auth.json` under `credential_pool.openai-codex`

#### Copilot 403 for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.
5. **Groq vs Grok (xAI) key confusion**: This is the #1 API-key troubleshooting case. Users generate a key on **Groq** (groq.com, for Llama/Mixtral/DeepSeek inference on LPUs, key prefix `gsk_`) but the config points to **xAI** (api.x.ai, for Grok models). The symptom is a clean HTTP 400 with message `Incorrect API key provided` — the endpoint doesn't recognize keys from the other platform. However, a **working** key can also return HTTP 403 `Your team ... has either used all available credits` if the xAI free-trial credits are exhausted. Two-stage diagnosis:
   - **HTTP 400** = wrong platform (regen key on correct console, or change `model.base_url`)
   - **HTTP 403** = correct platform but account has no credits left (add billing at console.x.ai/billing)
   
   Key formats: xAI issues both `gsk_...` (legacy) and `xai-...` (newer). Groq only `gsk_...`. You CANNOT distinguish by prefix alone.
   
   Fix: either regenerate the key on the correct platform (console.x.ai for Grok, console.groq.com for Groq) and set the matching `XAI_API_KEY` or `GROQ_API_KEY` env var, OR change `base_url` to match the platform the key was generated for.
   Reference + pricing comparison: `references/groq-vs-grok-provider-confusion.md`.
8. **xAI Grok models reject `reasoningEffect` parameter**: When using xAI Grok models (e.g. `grok-4.20-0309-reasoning`, `grok-4.20-reasoning`), Hermes sends `reasoningEffect` as an API parameter if `agent.reasoning_effort` is set to anything other than `none`. xAI's API does not support this parameter, causing this error:
   ```
   Model grok-4.20-0309-reasoning does not support parameter reasoningEffect
   ```
   **Fix:** Set `agent.reasoning_effort: none` in config.yaml — run `hermes config set agent.reasoning_effort none` or edit the file directly. This disables the reasoning-effort parameter entirely so xAI's API doesn't reject the request.
   
   **Provider-switching pitfall:** When switching FROM a provider that supports reasoning effort (e.g. DeepSeek, Anthropic) TO xAI/Grok, you must update TWO things: `model.base_url` (to `https://api.x.ai/v1`) AND `agent.reasoning_effort` (to `none`). Forgetting either one will cause API errors. Same applies when cloning profiles — check both settings.
6. **Model context window below 64K minimum (e.g. kimi-k2.6 at 32K)**: Hermes Agent requires at least 64K context. To bypass for smaller models, set TWO config keys:
   ```bash
   hermes config set model.context_length 65536
   hermes config set auxiliary.compression.context_length 65536
   ```
   The second key is needed because the auxiliary compression model inherits the main model and will also fail the 64K check. After setting both, restart the session (`/reset` or new invocation).
7. **Cloned profile uses wrong API endpoint**: When creating profiles with `--clone-from`, the `model.base_url` is copied from the source. If the new profile uses a different provider (e.g. switching from deepseek to kimi-coding-cn), the stale `base_url` will cause HTTP 401. Remove it:
   ```bash
   python3 -c "
   import yaml
   with open('~/.hermes/profiles/<name>/config.yaml') as f:
       c = yaml.safe_load(f)
   c['model'].pop('base_url', None)
   with open('~/.hermes/profiles/<name>/config.yaml', 'w') as f:
       yaml.dump(c, f)
   "
   ```

9. **OpenAI Codex `NoneType` error** → See `#### OpenAI Codex / OAuth provider` above for the correct diagnosis and fix (SDK bug, not model entitlement).

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `/skill name` or `hermes -s name`

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`
- **Platform ImportError on restart (e.g. WhatsApp)**: `/reset` only clears session context; ImportError means a **plugin or platform module fails at import time**. See `references/gateway-platform-importerror-debug.md` for the full diagnostic path. Quick check: `python3 -c "import importlib; importlib.import_module('<module>')"` and compare `platform_toolsets` in config.yaml against `hermes plugins list`.

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF-8 BOM config, test suite, line endings): see the dedicated **Windows-Specific Quirks** section above.

### send_message to WhatsApp fails — full resolution (2026-05-22, updated 2026-05-22)

`send_message(target="whatsapp")` returns `[error] "No home channel set"` even when WhatsApp receives messages. Three requirements must all be met:

1. **WhatsApp must be under `platforms:` in config.yaml, not as a top-level key.** If `whatsapp: {}` appears as a top-level key (e.g., after `web:`), `send_message` won't find it. Move it under `platforms:` — the gateway's `PlatformConfig` parser only scans the `platforms:` section.

2. **The top-level `WHATSAPP_HOME_CHANNEL` alone is insufficient.** The `PlatformConfig` object needs a `home_channel` sub-object with explicit `platform`, `chat_id`, and `name` fields. Set them via:
   ```bash
   hermes config set platforms.whatsapp.home_channel.platform whatsapp
   hermes config set platforms.whatsapp.home_channel.chat_id '<chat_id>'
   hermes config set platforms.whatsapp.home_channel.name <name>
   ```
   The chat ID format for self-chat mode is `<number>@lid`. After setting all three, restart the gateway:
   ```bash
   hermes gateway restart
   ```
   Verify with `send_message(action="list")` to confirm `whatsapp:Jianfeng (dm)` appears as a target. Then `send_message(target="whatsapp", message="...")` should succeed.

3. **Gateway must be restarted** after any platform config change. `send_message` reads `PlatformConfig` at gateway startup; changes don't hot-reload.

**Under the hood:** `PlatformConfig.home_channel` is a `HomeChannel` dataclass with fields `platform: Platform`, `chat_id: str`, `name: str`, `thread_id: Optional[str]`. The YAML nesting `platforms.whatsapp.home_channel.chat_id` maps to this structure. An empty `whatsapp: {}` block with a top-level `WHATSAPP_HOME_CHANNEL` key does NOT populate the dataclass — the gateway ignores top-level WhatsApp keys when building `PlatformConfig`.

### Cloudflare tunnel for webhook exposure (2026-05-17)

When a Hermes webhook needs to be reachable from another machine behind NAT/firewall, use Cloudflare's free tunnel:

```bash
# Start tunnel (runs until killed or VM reboots)
nohup cloudflared tunnel --url http://localhost:8644 --no-autoupdate > /tmp/cf-tunnel.log 2>&1 &

# Extract the trycloudflare.com URL (needs ~8s to establish)
sleep 8
grep -o 'https://[^.]*\.trycloudflare\.com' /tmp/cf-tunnel.log | tail -1
```

**Pitfalls:**
- Tunnel dies on VM reboot — must be restarted
- URL changes every restart (trycloudflare assigns random subdomain)
- `cloudflared` must be installed: `curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared`
- The `terminal(background=True)` tool sometimes captures no output from `cloudflared` — use `nohup ... > /tmp/cf-tunnel.log 2>&1 &` instead
### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

### `terminal()` curl returns empty output for webhook POSTs

When using `terminal(command="curl -X POST ...")` to hit a webhook endpoint, the output is often empty string with exit code -1 even when the request succeeds (status 202). The webhook endpoint IS reachable (GET to `/health` works).

**Fix**: Use Python's `urllib.request` in `execute_code()` instead:
```python
import urllib.request
req = urllib.request.Request(url, data=body, headers={...}, method="POST")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(resp.status, resp.read().decode())
```

This consistently returns `{"status":"accepted"}` for webhook POSTs.

### MCP server `--args` pitfall

`hermes mcp add --args` strips leading `--` from arguments, preventing them from reaching the MCP command. Example failure:

```bash
# This WILL NOT work — --repo is interpreted by Hermes CLI, not passed to the server
hermes mcp add code-review-graph --command=code-review-graph --args mcp --args "--repo=/path"
```

**Fix**: Add the server without repo args first, then edit `config.yaml` directly:

```bash
hermes mcp add code-review-graph --command=code-review-graph --args mcp
# Then edit ~/.hermes/config.yaml:
#   code-review-graph:
#     command: code-review-graph
#     args: [mcp, --repo, /path/to/repo]
```

After config edit, restart the gateway (`hermes gateway restart`) or `/reload-mcp` in-session.

### Disk space recovery on small VMs

When a 30G VM hits >90% disk usage, pip cache + uv cache + npm cache + __pycache__ typically account for 1-2G. See `references/vm-disk-space.md` for the full recovery playbook.

### RTK — token-saving CLI proxy (60-90% reduction)

[rtk](https://github.com/rtk-ai/rtk) (Rust Token Killer) is a Rust binary that filters and compresses terminal output before it reaches the LLM context. It has native Hermes support via a Python plugin adapter.

**Install RTK binary** (pick one):
```bash
brew install rtk                                              # macOS (recommended)
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh  # Linux/macOS
cargo install --git https://github.com/rtk-ai/rtk             # From source
```
Pre-built binaries also available at https://github.com/rtk-ai/rtk/releases.

**Install the Hermes plugin:**
```bash
rtk init --agent hermes
```

This creates `~/.hermes/plugins/rtk-rewrite/__init__.py` + `plugin.yaml` and adds `rtk-rewrite` to `plugins.enabled` in config.yaml.

**Verify:**
```bash
hermes plugins list        # rtk-rewrite should show "enabled"
rtk --version              # confirm RTK binary is in PATH
rtk rewrite "git status"   # test: should output "rtk git status" (exit 0 or 3)
```

**Restart required:** `/reset` or new session. Plugin hooks load at session start.

**How it works:** The plugin registers a `pre_tool_call` hook that intercepts every `terminal()` call, runs `rtk rewrite <command>`, and mutates the command before execution. Exit codes: 0 or 3 = rewrite produced (command gets mutated), 1 or 2 = passthrough (no RTK filter for this command), anything else = error (original command runs unchanged).

**Scope:** only `terminal()` tool calls are rewritten. Hermes built-in tools (`read_file`, `search_files`, etc.) bypass the shell entirely and are not affected. Commands already prefixed with `rtk`, compound shell commands, heredocs, and commands without an RTK filter pass through unchanged.

**Fail-open:** if `rtk` is not in PATH, `rtk rewrite` times out (2s), crashes, or returns an unexpected exit code, the original command executes normally. The plugin never blocks execution.

**What gets optimized** (100+ commands across these categories):
- File ops: `ls`, `cat`/read, `find`, `grep`
- Git: `status`, `diff`, `log`, `push`, `pull`, `commit`, `add`
- Test runners: `pytest`, `cargo test`, `go test`, `jest`, `vitest`, `playwright test`
- Build/lint: `cargo build`, `cargo clippy`, `ruff check`, `tsc`, `eslint`, `prettier`
- Containers: `docker ps/images/logs`, `docker compose ps`, `kubectl pods/logs`
- Package managers: `pnpm list`, `pip list`, `bundle install`
- GitHub CLI: `gh pr list`, `gh issue list`, `gh run list`
- AWS CLI, data tools (`json`, `deps`, `env`, `log`, `curl`)

Expected savings: 60-90% on common dev commands. In a typical 30-min session, ~118K tokens → ~24K tokens (-80%).

**Analytics** (opt-in telemetry, disabled by default):
```bash
rtk gain                     # summary stats
rtk gain --graph             # ASCII chart (last 30 days)
rtk gain --daily             # day-by-day breakdown
rtk gain --all --format json # JSON export
```

**Uninstall:**
```bash
rtk init -g --uninstall      # remove hook + RTK.md
hermes plugins disable rtk-rewrite  # disable plugin
# Optionally: rm -rf ~/.hermes/plugins/rtk-rewrite/
```

### Cron job delivers `[SILENT]` — no output reached the user (2026-05-30)

When a cron job's final response is `[SILENT]`, the job ran but the system suppressed delivery. Common causes and how to diagnose:

**1. Check the cron output file.** Every cron run saves its full prompt, context, and response to `~/.hermes/cron/output/<job_id>/YYYY-MM-DD_HH-MM-SS.md`. Look at the bottom for `## Response`:

```bash
tail -10 ~/.hermes/cron/output/<job_id>/<latest_file>.md
```

If it says `**[SILENT]**`, the agent chose not to deliver. If it shows a briefing, the content was delivered.

**2. Trace `context_from` chains.** If job B depends on job A's output (set via `context_from` in the cron config), check job A's output first. A missing or `[SILENT]` upstream job means job B started with empty context.

**3. Model-level NSFW guardrails suppress delivery.** This is the most common hidden cause. The agent may **write files to disk** (via tool calls) but still output `[SILENT]` because its model refuses to generate NSFW content as the final response. To check:

```bash
# Look for evidence of tool writes in the output file
grep -i "write_file\|saved\|saving" ~/.hermes/cron/output/<job_id>/<latest_file>.md
```

If tool writes succeeded but the response was `[SILENT]`, the model's guardrails blocked NSFW output. Known models and their NSFW behavior:

| Model/Provider | NSFW via tools? | NSFW as final response? |
|----------------|:---------------:|:-----------------------:|
| deepseek-v4-pro/flash | ✅ Writes files | ❌ Refuses model output |
| grok-4.20-0309-reasoning (xAI) | ✅ Writes files | ✅ Generates output |
| kimi-k2.6 | ✅ Writes files | ✅ Generates output |

**Fix:** Switch the profile's model to one without NSFW filtering. For a profile used by cron:

```bash
# 1. Change model to one that passes NSFW
hermes config set model.default grok-4.20-0309-reasoning   # on the profile
hermes config set model.provider xai

# 2. Ensure reasoning_effort is none (xAI rejects this param)
hermes config set agent.reasoning_effort none
```

**4. File delivery vs. response delivery are separate paths.** The cron agent writes files via tool calls (skips output guardrails), but the final model response is what gets delivered to the user. A job that writes the briefing file but outputs `[SILENT]` successfully saved the data but never sent it. To verify file was written, check the profile's memories or the path the cron prompt specified.

### SkillClaw — automatic skill evolution for Hermes

[SkillClaw](https://github.com/AMAP-ML/SkillClaw) (1400+ stars) auto-evolves, deduplicates, and improves Hermes skills from real session data. Runs as a local LLM proxy on port 30000 that intercepts requests, records sessions, and refines skills in the background.

```bash
# Install
git clone https://github.com/AMAP-ML/SkillClaw.git && cd SkillClaw
bash scripts/install_skillclaw.sh && source .venv/bin/activate
# Prerequisite (Debian/Ubuntu): sudo apt install python3.11-venv

# Configure
skillclaw setup   # interactive wizard
# Or manually: ~/.skillclaw/config.yaml (nested llm.*, proxy.port, claw_type, skills.*)

# Start / monitor
skillclaw start --daemon
skillclaw status
skillclaw doctor hermes

# Stop / restore
skillclaw stop
skillclaw restore hermes   # revert ~/.hermes/config.yaml
```

On start, rewrites `~/.hermes/config.yaml`: model→skillclaw-model, base_url→http://127.0.0.1:30000/v1, provider→custom. Backup saved to `~/.skillclaw/backups/hermes/config.latest.yaml`. **Restart Hermes** (`/reset`) for the proxy to take effect.

**Pitfall:** `skillclaw config set llm.api_key "sk-..."` may reject API key values with special characters. Workaround: use `python3 -c "import yaml; cfg=yaml.safe_load(open('~/.skillclaw/config.yaml')); cfg['llm']['api_key']='...'; yaml.dump(cfg, open('~/.skillclaw/config.yaml','w'))"`.

Full config reference: `references/skillclaw-config.yaml`

### write_file corrupts markdown with line-number prefixes (2026-05-18)

When writing `.md` files, `write_file` sometimes prepends line-number metadata (`     1|`) to each line. This silently corrupts files parsed by regex tools.

**Fix**: Use `execute_code` with `open().write()` for machine-parsed files. Human-read files are fine with `write_file`.
Hermes has **two separate MCP paths** that are often mixed up:
- **MCP Client** (`tools/mcp_tool.py`): Hermes *connects to* external MCP servers. Configured via `mcp_servers:` in `config.yaml`. This is **not** a server you can point Claude Desktop at.
- **MCP Server** (`mcp_serve.py`): Exposes Hermes conversations as MCP tools. Started with `hermes mcp serve`. This **is** what you point Claude Desktop at.

If you want to expose a local knowledge base (markdown/PDF) as an MCP server to external clients, you need a **standalone FastMCP script** — not `mcp_tool.py`. See `references/migration-and-mcp.md` for a working template.

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `~/.hermes/sessions/` or `hermes sessions browse` |
| Source code | `~/.hermes/hermes-agent/` |
| Replacing backend services with Hermes API | `references/replace-backend-with-hermes-api.md` |

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

### Adding a Tool (3 files)

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Add to `toolsets.py`** → `_HERMES_CORE_TOOLS` list.

Auto-discovery: any `tools/*.py` file with a top-level `registry.register()` call is imported automatically — no manual list needed.

All handlers must return JSON strings. Use `get_hermes_home()` for paths, never hardcode `~/.hermes`.

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- Use `-o 'addopts='` to clear any baked-in pytest flags

**Windows contributors:** `scripts/run_tests.sh` currently looks for POSIX venvs (`.venv/bin/activate` / `venv/bin/activate`) and will error out on Windows where the layout is `venv/Scripts/activate` + `python.exe`. The Hermes-installed venv at `venv/Scripts/` also has no `pip` or `pytest` — it's stripped for end-user install size. Workaround: install pytest + pytest-xdist + pyyaml into a system Python 3.11 user site (`/c/Program Files/Python311/python -m pip install --user pytest pytest-xdist pyyaml`), then run tests directly:

```bash
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/tools/test_foo.py -v --tb=short -n 0
```

Use `-n 0` (not `-n 4`) because `pyproject.toml`'s default `addopts` already includes `-n`, and the wrapper's CI-parity story doesn't apply off-POSIX.

**Cross-platform test guards:** tests that use POSIX-only syscalls need a skip marker. Common ones already in the codebase:
- Symlink creation → `@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require elevated privileges on Windows")` (see `tests/cron/test_cron_script.py`)
- POSIX file modes (0o600, etc.) → `@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX mode bits not enforced on Windows")` (see `tests/hermes_cli/test_auth_toctou_file_modes.py`)
- `signal.SIGALRM` → Unix-only (see `tests/conftest.py::_enforce_test_timeout`)
- Live Winsock / Windows-specific regression tests → `@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific regression")`

**Monkeypatching `sys.platform` is not enough** when the code under test also calls `platform.system()` / `platform.release()` / `platform.mac_ver()`. Those functions re-read the real OS independently, so a test that sets `sys.platform = "linux"` on a Windows runner will still see `platform.system() == "Windows"` and route through the Windows branch. Patch all three together:

```python
monkeypatch.setattr(sys, "platform", "linux")
monkeypatch.setattr(platform, "system", lambda: "Linux")
monkeypatch.setattr(platform, "release", lambda: "6.8.0-generic")
```

See `tests/agent/test_prompt_builder.py::TestEnvironmentHints` for a worked example.

### Extending the system prompt's execution-environment block

Factual guidance about the host OS, user home, cwd, terminal backend, and shell (bash vs. PowerShell on Windows) is emitted from `agent/prompt_builder.py::build_environment_hints()`. This is also where the WSL hint and per-backend probe logic live. The convention:

- **Local terminal backend** → emit host info (OS, `$HOME`, cwd) + Windows-specific notes (hostname ≠ username, `terminal` uses bash not PowerShell).
- **Remote terminal backend** (anything in `_REMOTE_TERMINAL_BACKENDS`: `docker, singularity, modal, daytona, ssh, vercel_sandbox, managed_modal`) → **suppress** host info entirely and describe only the backend. A live `uname`/`whoami`/`pwd` probe runs inside the backend via `tools.environments.get_environment(...).execute(...)`, cached per process in `_BACKEND_PROBE_CACHE`, with a static fallback if the probe times out.
- **Key fact for prompt authoring:** when `TERMINAL_ENV != "local"`, *every* file tool (`read_file`, `write_file`, `patch`, `search_files`) runs inside the backend container, not on the host. The system prompt must never describe the host in that case — the agent can't touch it.

Full design notes, the exact emitted strings, and testing pitfalls:
`references/prompt-builder-environment-hints.md`.

**Refactor-safety pattern (POSIX-equivalence guard):** when you extract inline logic into a helper that adds Windows/platform-specific behavior, keep a `_legacy_<name>` oracle function in the test file that's a verbatim copy of the old code, then parametrize-diff against it. Example: `tests/tools/test_code_execution_windows_env.py::TestPosixEquivalence`. This locks in the invariant that POSIX behavior is bit-for-bit identical and makes any future drift fail loudly with a clear diff.

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
