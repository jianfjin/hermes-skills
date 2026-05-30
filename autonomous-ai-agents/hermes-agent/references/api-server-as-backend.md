# Using Hermes API Server as a Programmatic Backend

**Updated:** 2026-05-30

## Discovery

The Hermes Gateway API Server (port 8642 by default) exposes an **OpenAI-compatible `/v1/chat/completions`** endpoint. This means ANY HTTP client — frontend SPA, mobile app, CI/CD pipeline, another agent — can call Hermes with the same API format as OpenAI.

```
GET  /health                    → {"status": "ok", "platform": "hermes-agent"}
POST /v1/chat/completions       → OpenAI chat completion format
```

## Verification

```bash
# Health check
curl http://localhost:8642/

# Chat completion
curl -s http://localhost:8642/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sekret" \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

Response format:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1780116960,
  "model": "deepseek-v4-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "..."   // ← this is your answer
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 16156,
    "completion_tokens": 81,
    "total_tokens": 16237
  }
}
```

## Config

The API Server is configured under `platforms.api_server` in config.yaml:

```yaml
platforms:
  api_server:
    enabled: true
    port: 8642
    key: sekret              # Authorization: Bearer <key>
    cors_origins:
      - '*'
```

The auth key goes in the HTTP `Authorization: Bearer <key>` header.

## Architectural Patterns

### Pattern A: Frontend Calls Hermes Directly

```
User → Frontend (Express/Next.js/React)
         → POST localhost:8642/v1/chat/completions
```

**Best when:** You control the frontend code and want zero intermediate services.

**Implementation (Node.js/TypeScript):**

```typescript
// front-end/server.ts — replace backend proxy with direct Hermes call
const HERMES_API_URL = process.env.HERMES_API_URL || "http://localhost:8642";
const HERMES_API_KEY = process.env.HERMES_API_KEY || "sekret";

app.post("/api/chat", async (req, res) => {
  const { message, history = [] } = req.body;
  
  const response = await fetch(`${HERMES_API_URL}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${HERMES_API_KEY}`,
    },
    body: JSON.stringify({
      model: "deepseek-v4-flash",
      messages: [
        ...history.map(m => ({ role: m.role, content: m.content })),
        { role: "user", content: message },
      ],
    }),
  });
  
  const data = await response.json();
  const answer = data.choices?.[0]?.message?.content || "";
  
  res.json({
    answer,
    sources: [{ document: "Hermes Agent", section: "AI Assistant" }],
    session_id: req.body.session_id,
  });
});
```

**TypeScript tip for OpenAI response types:**

```typescript
interface OpenAIChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: { role: string; content: string };
    finish_reason: string;
  }>;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}
```

### Pattern B: Thin Proxy Layer (Preserves Existing Backend Contract)

```
User → Frontend (unchanged)
         → POST localhost:8001/chat (existing RAG server)
              → Proxy layer → POST localhost:8642/v1/chat/completions
```

**Best when:** You can't change frontend code, need to keep existing API contract, or want caching/logging at the proxy level.

**Implementation (Python FastAPI):**

```python
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
HERMES_URL = "http://localhost:8642/v1/chat/completions"
HERMES_KEY = "sekret"

class ChatRequest(BaseModel):
    message: str
    history: list = []
    session_id: str = "default"

class ChatResponse(BaseModel):
    answer: str
    sources: list
    session_id: str

@app.post("/chat")
async def chat(req: ChatRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            HERMES_URL,
            headers={"Authorization": f"Bearer {HERMES_KEY}"},
            json={
                "model": "deepseek-v4-flash",
                "messages": [
                    *[{"role": m["role"], "content": m["content"]} for m in req.history],
                    {"role": "user", "content": req.message},
                ],
            },
        )
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]

    return ChatResponse(
        answer=answer,
        sources=[{"document": "Hermes Agent", "section": "AI Assistant"}],
        session_id=req.session_id,
    )
```

### Pattern C: Webhook (Async, NOT for synchronous API)

```
User → Frontend → POST /webhooks/edm-chat → Hermes processes → delivers to chat
```

**Not recommended** for synchronous request/response. Webhooks are fire-and-forget — they trigger an agent run and deliver the result to a target (Telegram, log, etc.), don't return it to the caller. Use only for async notification/alert flows.

## Pitfalls

### Session Management

Hermes API Server is **stateless per request** — it doesn't maintain session context between calls. To maintain conversation continuity:

- Pass the full message history in each `messages` array
- Let the model manage context via `messages` ordering
- Frontend keeps the history (in memory or localStorage) and sends it each time

### Sources/Tracing

The OpenAI response format has no `sources` field. If your frontend expects citation tracking:

- **Prompt-level:** Instruct Hermes via system prompt: "Always cite your sources at the end of your answer using [Source: document-name] format."
- **Post-processing:** Parse the response content for citation markers
- **Hybrid:** Keep the EHDSKGRetriever on the side for source extraction, pass results as context in the system message

### Model vs Provider

The `model` field in the request body selects which model Hermes uses. Available models depend on the gateway's configured model/provider. Check with the active Hermes instance or config.

### Auth Header

Required: `Authorization: Bearer <key>`
The key matches `platforms.api_server.key` in `config.yaml`. If key is empty/absent, the API server may deny all requests.

### CORS

If the frontend calls the API server directly from the browser (not through a proxy), CORS must be configured:
```yaml
platforms:
  api_server:
    cors_origins:
      - 'http://localhost:5173'    # Vite dev server
      - 'https://yourdomain.com'
```

## When to Use Each Pattern

| Pattern | Frontend Change | Backend Change | Latency | Complexity | Best For |
|---------|:--------------:|:--------------:|:------:|:---------:|----------|
| A: Direct | 12 lines | 0 | 1 hop | Low | New projects, controlled frontend |
| B: Proxy | 0 | Rewrite rag_server.py | 2 hops | Medium | Existing backend contract |
| C: Webhook | Full rewrite | N/A | Async | Medium | Notifications, not API |
