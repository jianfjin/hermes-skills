# Replacing a Backend LLM/RAG Service with Hermes API Server

## When to Use This Pattern

You have an existing backend service (LLM synthesis, RAG query, KG lookup) that serves a frontend, and you want to replace it with Hermes Agent's built-in API Server so the frontend benefits from Hermes' skills, memory, and tool ecosystem.

## Prerequisites

- Hermes API Server must be running (check: `curl http://localhost:8642/` → `{"status":"ok"}`)
- Default port: `8642`, but configurable via config.yaml → `api_server.port`
- Default auth key: configurable via config.yaml → `api_server.key`

## Architecture

The Hermes API Server exposes an **OpenAI-compatible** `/v1/chat/completions` endpoint. Any code that can call OpenAI's API can call Hermes instead.

## Three Integration Approaches

### Approach A: Call Hermes Directly from Frontend (Recommended)

**Strategy:** Change the frontend's API proxy to point at Hermes instead of the old backend.

**Request transformation:**
```
Old format (custom):            New format (OpenAI-compatible):
{                                {
  message,             →          model: "deepseek-v4-flash",
  history?,                      messages: [
  session_id                     ...history,
}                                {role: "user", content: message}
                                 },
```

**Response transformation:**
```
OpenAI response format:          Frontend-expected format:
{                                {
  choices: [{                    answer: choices[0].message.content,
    message: {content: "..."}    sources: [...],
  }]                             session_id: "..."
}                              }
```

**Key code (TypeScript/Node.js):**
```typescript
const hermesApiUrl = process.env.HERMES_API_URL || "http://localhost:8642";
const hermesApiKey = process.env.HERMES_API_KEY || "sekret";

const messages: { role: string; content: string }[] = [];
if (history) for (const m of history) messages.push({ role: m.role, content: m.content });
messages.push({ role: "user", content: message });

const response = await fetch(`${hermesApiUrl}/v1/chat/completions`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${hermesApiKey}`,
  },
  body: JSON.stringify({ model: "deepseek-v4-flash", messages }),
});
const data = await response.json();
const answer = data.choices?.[0]?.message?.content || "";
```

**Pros:** Minimal diff (~12 lines), zero new services, easy toggle via env var.
**Cons:** Response format changes — need a lightweight adapter on the frontend.

### Approach B: Keep Proxy Service, Swap Backend

**Strategy:** Keep the existing backend server running (same port, same API), but replace its LLM/RAG internal logic with a forward to Hermes API Server.

```python
import httpx

async with httpx.AsyncClient(timeout=60.0) as client:
    resp = await client.post(
        f"{hermes_api_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {hermes_api_key}"},
        json={
            "model": "deepseek-v4-flash",
            "messages": messages,
        },
    )
    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
```

**Pros:** Frontend unchanged — same port, same response schema.
**Cons:** Extra HTTP hop, still runs a separate process.

### Approach C: Webhook (Not for Sync APIs)

Hermes webhooks (`hermes webhook subscribe`) are asynchronous — they deliver results to a separate channel (Telegram, Discord, log), not back to the HTTP response. Not suitable for synchronous chat APIs. Use Approaches A or B instead.

## Env-Var Toggle Pattern

Always implement a toggle so you can fall back to the original backend:

**Frontend (TypeScript):**
```typescript
const useHermesApi = process.env.USE_HERMES_API !== "false";
```

**Backend (Python):**
```python
use_hermes_proxy = os.getenv("USE_HERMES_PROXY", "true").lower() == "true"
```

This lets you flip between old and new backends without redeploying code.

## Pitfalls

- **Session continuity:** Hermes API Server is stateless. Pass full history in the messages array. The frontend must manage its own session state.
- **Source tracking:** The original RAG/KG service provided source citations (document/section/layer). With Hermes, instruct the model to output inline citations in its response.
- **API format mismatch:** OpenAI format uses `choices[0].message.content`. If the frontend expects a different response shape, add a response adapter.
- **Timeout:** Set a generous timeout (60s+) for the Hermes API call. Model inference can be slow for complex queries.
- **Fallback design:** The toggle env var should default ON (hermes) but allow easy flip back to the original backend.
