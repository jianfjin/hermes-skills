# kimi-k2.6 Quirks when used as a Hermes Profile model

## Context Window Gate (32K < 64K)

kimi-k2.6 has a 32,768-token context window. Hermes Agent enforces a 64,000-token
minimum on startup. The model initialization fails with:

```
Failed to initialize agent: Model kimi-k2.6 has a context window of 32,768
tokens, which is below the minimum 64,000 required by Hermes Agent.
```

### Fix: two-tier context_length override

Setting `model.context_length` alone is insufficient. The model check passes,
but the auxiliary compression model (defaults to same model) fails next:

```
Failed to initialize agent: Auxiliary compression model kimi-k2.6 has a context
window of 32,768 tokens, which is below the minimum 64,000 required by Hermes
Agent. Choose a compression model with at least 64K context (set
auxiliary.compression.model in config.yaml), or set
auxiliary.compression.context_length to override the detected value if it is wrong.
```

**Both overrides required:**

```bash
<profile> config set model.context_length 65536
<profile> config set auxiliary.compression.context_length 65536
```

## base_url Contamination from --clone-from

When `hermes profile create --clone-from default` and the source profile uses
a different provider (e.g., default=deepseek, new profile=kimi-coding-cn), the
cloned `model.base_url` still points to the old provider's endpoint:

```yaml
model:
  default: kimi-k2.6
  provider: kimi-coding-cn
  base_url: https://api.deepseek.com/v1    # ← stale from clone
```

This causes HTTP 401 authentication failures because the kimi API key is sent
to DeepSeek's endpoint. The error:

```
⚠️ API call failed: AuthenticationError [HTTP 401]
   🔌 Provider: kimi-coding-cn  Model: kimi-k2.6
   🌐 Endpoint: https://api.deepseek.com/v1
   📝 Error: HTTP 401: Authentication Fails
```

**Fix:** Remove the `base_url` line from the profile's config.yaml `model:` section,
or set it to the correct provider endpoint. The provider's built-in endpoint will
be used if `base_url` is absent.

## kimi API Key

The `kimi-coding-cn` provider uses `KIMI_CN_API_KEY` from `.env` (not `KIMI_API_KEY`).
The legacy `KIMI_API_KEY` env var is commented out in the default `.env` — only
`KIMI_CN_API_KEY` is active.
