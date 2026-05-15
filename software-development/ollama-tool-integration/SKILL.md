---
name: ollama-tool-integration
description: Integrating local LLMs with external tool bridges (Search, Vision) and maintaining streaming UIs.
category: software-development
---

# Integrating Local LLMs with External Tools (Ollama + Search Bridges)

This skill describes the process of replacing a cloud-based LLM SDK (like Google Gemini) with a local Ollama instance while maintaining advanced capabilities like web search and multimodal (image) support.

## Trigger Conditions
- Migrating a project from a managed AI SDK (Gemini, OpenAI) to a local Ollama setup.
- Need to implement "Tool Use" (like search) for an Ollama model that doesn't have native tool-calling plugins.
- Maintaining a streaming UI while performing multi-step asynchronous operations (e.g., Search -> Respond).

## Workflow

### 1. Model Selection
Ensure the local model supports the required modalities. For vision, use multimodal models like `gemma4` or `llava`.

### 2. Implementing the Search Bridge
Since Ollama is a model runner, not a platform, you must build the bridge manually:
- **API Selection**: Use a search API (e.g., Tavily, Serper).
- **Protocol Definition**: Define a clear trigger in the system prompt (e.g., `{"search": "query"}`).
- **Manual Tool Loop**:
    1. Model generates a "thought" containing the trigger.
    2. Code intercepts the trigger and executes the external API call.
    3. Search results are appended to the conversation history as a new `user` message.
    4. Model is called again to generate the final answer based on the results.

### 3. Handling Multimodal Data
Ollama handles images differently than SDKs. Pass the base64 encoded image (without the MIME prefix) in the `images` array of the request body:
```json
{
  "model": "model_name",
  "messages": [...],
  "images": ["base64_data_here"],
  "stream": true
}
```

### 4. Maintaining Streaming UIs
To prevent the UI from breaking during a "Search -> Response" transition:
- Use an **Async Generator** in TypeScript/JavaScript.
- Yield the first "thought" stream.
- After the first stream finishes, perform the search.
- Start a second stream for the final answer and yield those chunks immediately after.
- This makes the "Tool Use" look like a continuous stream to the end-user.

## Pitfalls
- **Statelessness**: Unlike SDKs that manage "Chat Sessions," Ollama's `/api/chat` is stateless. You must maintain the `messages` array manually in the application state.
- **Prompt Leaks**: Users might see the `{"search": "..."}` JSON if not filtered. Consider guiding the model to put tool calls in a specific block or filtering the stream.
- **MIME Prefixes**: Always strip `data:image/png;base64,` from images before sending to Ollama.

## Verification
- Verify the model triggers the search JSON when asked about specific locations.
- Confirm the final answer incorporates actual data from the search API.
- Test image uploads and verify the model describes the image correctly.
