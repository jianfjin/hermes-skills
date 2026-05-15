---
name: ollama-tool-bridge
description: Workflow for replacing a cloud-based LLM with a local Ollama model while maintaining tool-use capabilities via a middleware bridge.
category: software-development
---

# Local LLM Tool-Use Bridge (Ollama + External API)

## Description
Workflow for replacing a cloud-based LLM (e.g., Gemini) with a local Ollama model while maintaining tool-use capabilities (like web search) through a middleware "bridge".

## Trigger
When a project needs to shift from a cloud model to a local model but requires external tool integration (Search, DB, etc.) that the local model cannot perform natively.

## Steps
1. **Identify Model**: Select a multimodal local model (e.g., `gemma4`, `llava`) via Ollama.
2. **Implement API Bridge**:
    - Create a service wrapper around Ollama's `/api/chat` or `/api/generate`.
    - Map the cloud-based tool calls to local "keyword" or "JSON" triggers in the system prompt.
3. **Build the Execution Loop**:
    - **Step A (Reasoning)**: Send a prompt to the local model.
    - **Step B (Detection)**: Scan the streamed response for a specific trigger (e.g., `{"search": "query"}`).
    - **Step C (Action)**: Intercept the stream, call the external API (e.g., Tavily), and fetch results.
    - **Step D (Synthesis)**: Append the tool results to the conversation history as a "system" or "user" message and trigger a second call to the model for the final response.
4. **Handle Multimodality**:
    - Convert image inputs to base64.
    - Pass them in the `images` array of the Ollama request body.

## Pitfalls
- **Statelessness**: Ollama's API is often stateless; you must maintain and send the full `messages` array in every call.
- **Hallucinations**: Local models may hallucinate tool calls if the system prompt isn't strict. Use few-shot examples.
- **Latency**: Two-pass loops (Search -> Respond) double the latency. Ensure the frontend handles "Thinking..." states.

## Verification
- Verify the model triggers the search command.
- Confirm the API results are correctly injected into the second pass.
- Check that image base64 encoding is correctly stripped of the data URI prefix before being sent to Ollama.