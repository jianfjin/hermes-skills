# Groq vs Grok (xAI) Provider Confusion

## The Problem

Users frequently confuse **Groq** (groq.com) with **Grok** / **xAI** (x.ai). The names are phonetically similar, both serve AI models, and both generate API keys. A key generated on one platform will fail (HTTP 400 "Incorrect API key") when used against the other's endpoint.

## Quick Comparison

| | **Groq** | **Grok / xAI** |
|---|---|---|
| Company | Groq Inc. | xAI (Elon Musk) |
| Website | console.groq.com | console.x.ai |
| API endpoint | api.groq.com/openai/v1 | api.x.ai/v1 |
| Key prefix | `gsk_` (56 chars) | `gsk_` or `xai-` (56-64 chars) |
| Models | Llama, Mixtral, DeepSeek, Gemma, Qwen (open-source) | grok-4.20-reasoning, grok-4.20, grok-3.5 (proprietary) |
| Free tier | Yes (rate-limited, generous daily quota) | Initial $5-$25 credits — **one-time**, then paid |
| Pricing (input) | Free (varies by model) | $1.25/M tokens (grok-4.20) |
| Pricing (output) | Free | $2.50/M tokens |
| Content policy | Varies by model (open-source) | "Minimally useful censorship" — much freer than DeepSeek, Claude |
| Hermes env var | `GROQ_API_KEY` | `XAI_API_KEY` |
| Hermes base_url | `https://api.groq.com/openai/v1` | `https://api.x.ai/v1` |

## Key Prefixes

| Key format | Platform | Example |
|------------|----------|---------|
| `gsk_...` (56 chars) | **Groq** | `gsk_V6D...4teM` |
| `gsk_...` (56 chars) | **xAI** (older) | `gsk_...` |
| `xai-...` (56-64 chars) | **xAI** (newer) | `xai-HKgD...rzNI` |

**You cannot distinguish by prefix alone** — both platforms have used `gsk_`. Check which console the key was generated on. As of mid-2026, xAI issues `xai-` keys but legacy `gsk_` keys still work.

## Two-Stage Failure Diagnosis

The error changes meaning depending on which stage the key reaches:

### Stage 1: HTTP 400 — Wrong platform
`Incorrect API key provided: gs...eM` — the endpoint doesn't recognize the key at all. This means the key was generated for the **other** platform (Groq key on xAI endpoint, or vice versa).

### Stage 2: HTTP 403 — No credits (xAI only)
`Your team ... has either used all available credits or reached its monthly spending limit. To continue making API requests, please purchase more credits or raise your spending limit.`

The key IS valid — authentication passed — but the account's free credits are exhausted. xAI new accounts get a one-time credit grant (typically $5-$25). Once spent, you must add billing at https://console.x.ai/billing.

If a Groq key reaches this stage, the user has somehow gotten a Groq endpoint to pass auth but hit a quota limit (rare — Groq is generous with free tier).

### Diagnostic Flow

```
Is it HTTP 400 "Incorrect API key"?
  └─ Yes → Key is for the wrong platform (Groq ↔ xAI mixup)
  └─ No, it's HTTP 403 "no credits / monthly limit"?
       └─ Key is valid but account has no credits left
       └─ Go to console.x.ai/billing to check/charge
```

## Price Comparison (for when xAI credits run out)

| Model | Input/M | Output/M | Cache read/M | Context |
|-------|---------|----------|-------------|---------|
| Grok-4.20 (xAI) | $1.25 | $2.50 | $0.20 | 2M |
| DeepSeek V4 Flash | $0.14 | $0.28 | $0.02 | 1M |
| DeepSeek V4 Pro | $0.42 | $1.06 | $0.06 | 1M |

Grok is ~9x more expensive than DeepSeek Flash. Typical conversation (10K in + 2K out): ~$0.018 vs ~$0.002.

## Why Users Switch

- **FROM DeepSeek**: Content restrictions — DeepSeek (Chinese company) is heavily censored on political and social topics. Grok is much more permissive ("minimally useful censorship").
- **FROM Claude**: Also somewhat restricted; Grok is freer but less refined for code.
- **TO Groq (free)**: When xAI credits run out and user doesn't want to pay. Groq runs open-source models at excellent speed, but models lack Grok's content freedom.

## Provider Switching Workflow

To switch between providers in Hermes:

```bash
# Switch to xAI/Grok:
hermes config set model.base_url https://api.x.ai/v1
hermes config set model.default grok-4.20-reasoning
hermes config set model.provider xai

# Switch to DeepSeek:
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek

# Switch to Groq (free open-source models):
hermes config set model.base_url https://api.groq.com/openai/v1
hermes config set model.default llama-4-scout-17b-16e-instruct
hermes config set model.provider groq
```

Also set the corresponding `*_API_KEY` env var in `~/.hermes/.env`. After switching, `/reset` to start a fresh session.

**Critical — reasoning_effort:** xAI Grok models do NOT support the `reasoningEffect` parameter. If `agent.reasoning_effort` is set to anything other than `none` (e.g. `medium` from a prior DeepSeek or Anthropic config), Hermes will send it and xAI will reject with `Model ... does not support parameter reasoningEffect`. Always check and set:
```bash
hermes config set agent.reasoning_effort none
```
This applies to both the main config and any profile configs when switching providers. The fix is to disable reasoning effort entirely — xAI handles reasoning natively without this parameter.

## Steps

1. Read the current base_url:
   ```bash
   grep base_url ~/.hermes/config.yaml
   ```

2. Check which platform the key was generated on:
   - Has `console.x.ai` login / billing? → xAI
   - Has `console.groq.com` login / billing? → Groq
   - Look at browser history / password manager entries

3. Verify the key is in the right env var:
   - For xAI: `XAI_API_KEY` in `~/.hermes/.env`
   - For Groq: `GROQ_API_KEY` in `~/.hermes/.env`

4. Check whether the error is HTTP 400 (wrong platform) or HTTP 403 (no credits):
   - 400 → fix platform mismatch (regen key or change `model.base_url`)
   - 403 → visit console.x.ai/billing to add payment method

## Fix Options

### Option A: Regenerate on the correct platform
- For Grok models: go to https://console.x.ai, generate API key, set `XAI_API_KEY` in `.env`
- For Groq: keep the existing key, change `model.base_url` to `https://api.groq.com/openai/v1`

### Option B: Change base_url to match the key
```bash
hermes config set model.base_url https://api.groq.com/openai/v1
# Or for xAI:
hermes config set model.base_url https://api.x.ai/v1
```

### Option C: Use the key on the correct platform (switch models)
If the user generated a Groq key but wants xAI Grok models — they need a separate xAI key. There is no cross-platform key sharing.

### Option D: Pay for credits (xAI only)
Visit https://console.x.ai/billing to add a payment method. Minimum $5 top-up.

## Verification

After fixing, test the key directly:
```bash
python3 -c "
import urllib.request, json
with open('/home/jianfjin/.hermes/.env') as f:
    for line in f:
        if line.startswith('XAI_API_KEY=') or line.startswith('GROQ_API_KEY='):
            key = line.strip().split('=', 1)[1]
            break
# Test with models list endpoint
url = 'https://api.x.ai/v1/models'  # or https://api.groq.com/openai/v1/models
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        models = [m['id'] for m in data.get('data', [])]
        print(f'OK - {len(models)} models')
        for m in models[:5]: print(f'  {m}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:200]
    print(f'FAILED: HTTP {e.code}: {body}')
"
```

- HTTP 200 → key is valid and endpoint is correct
- HTTP 400 → wrong platform (Incorrect API key)
- HTTP 403 → correct platform but no credits left
