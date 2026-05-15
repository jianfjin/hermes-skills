---
name: neuro-symbolic-persona-integration
description: Integrating high-fidelity personas and structured symbolic knowledge for expert advisory boards and compliance agents.
---

# Neuro-Symbolic Persona & Knowledge Integration

## Description
A workflow for integrating high-fidelity human personas (e.g., Elon Musk, Zhang Xuefeng) and structured domain-specific knowledge (e.g., EHDS regulations) into an LLM agent framework to create specialized "Advisory Boards" or "Audit Agents".

## Trigger Conditions
- When the user requests a team of expert personas to analyze a project.
- When building a "Cognitive Dual-Track" system (combining Vector and Graph/Symbolic data).
- When creating an Agent that must act as a legal/compliance auditor based on rigid rules.

## Steps

### 1. Persona Matrix Construction
Instead of simple prompts, create detailed Persona Markdown files in a dedicated directory (e.g., `~/.hermes/personas/`).
- **Required Fields**: Core Identity, Biographical Dimensions, Psychological Profile, Strategic Function (e.g., "First Principles Architect" vs "Realism Auditor"), and a specific "Voice" guideline.
- **Logic**: Ensure personas have conflicting archetypes (e.g., Idealist vs. Pragmatist) to force a dialectic process during decision-making.

### 2. Symbolic Knowledge Base (SKB) Design
For high-stakes compliance (like EHDS), avoid relying solely on Vector RAG. Create a symbolic layer:
- **SPO Triplets**: Define rules as `[Entity] -> [Relationship] -> [Constraint]` (e.g., `[Purpose] -> MUST_NOT_BE -> [Commercial Marketing]`).
- **Risk Mapping**: Create a keyword-to-risk-level mapping (e.g., "Broad research" $\rightarrow$ High Risk).
- **Optimization Maps**: Provide direct mapping for "Wrong Phrase" $\rightarrow$ "Compliant Phrase" to enable "Buzzword Optimization".

### 3. The G-RAG Pipeline (Neuro-Symbolic)
Implement a retrieval flow that transitions from intuition to logic:
- **Semantic Trigger**: Use Vector Search to find similar cases/contexts.
- **Relational Expansion**: Map the Vector ID to a Graph Node ID $\rightarrow$ Traverse the Symbolic Rules.
- **Synthesis**: Feed the [Semantic Fragment + Symbolic Constraint] into the Auditor Persona.

## Pitfalls & Lessons Learned
- **Automation Failure**: High-fidelity persona creation via automated delegation can fail due to context size or API instability. Manual "Surgical Ingestion" (creating curated .md files) is more reliable.
- **Siloed Knowledge**: Simple Vector RAG often "hallucinates" compliance. Forced alignment with a Symbolic KB (SPO triplets) is mandatory for legal/regulatory agents.
- **Installation Deadlocks**: Complex TS/JS monorepos (like Paperclip) can experience `pnpm` timeouts. Use `--no-frozen-lockfile` or fallback to global `npm` path exports to force progress.

## Verification
- Check if the Agent can identify a specific rule violation from the SKB.
- Verify if the Persona's voice remains consistent with the defined "Psychological Profile".
