---
name: debug-uv-environment-corruption
description: Process for resolving Python environment failures in VM instances, specifically when dealing with 'externally-managed-environment' errors, disk space exhaustion, and corrupted config files.
version: 1.0.0
author: He Mi Si
tags: [python, uv, venv, linux, debugging, deployment]
---

# Debugging UV and Python Environment Corruption

## Overview
When deploying Python applications via `uv` or `pip` in restricted VM environments, you may encounter a "perfect storm" of failures: disk space exhaustion causing partial installs, `externally-managed-environment` (PEP 668) blocks, and config file pollution (e.g., line numbers injected into TOML).

## Trigger Conditions
- `Succeeded` installation but `ModuleNotFoundError` occurs at runtime.
- `uv` failures with "No space left on device" during heavy dependency (torch/cuda) extraction.
- `pip` failure with `externally-managed-environment` error.
- `TOML parse error` in `pyproject.toml` due to unexpected characters or numbering.

## Systematic Recovery Workflow

### 1. Disk Space Recovery
Before any installation, clear the massive caches that often clog VMs.
```bash
rm -rf ~/.cache/uv ~/.cache/pip ~/.cache/huggingface
```

### 2. Configuration De-pollution
If `pyproject.toml` or `requirements.txt` contains line numbers (e.g., ` 1| [project]`), do NOT use recursive edits. Use an absolute overwrite with a pure string.
- **Avoid:** Using `patch` or `sed` on heavily polluted files.
- **Action:** Write the entire clean content back using a `write_file` tool.

### 3. Breaking the PEP 668 Block
When the system prevents `pip install` or `pip uninstall` globally and venvs are corrupted:
- **The "Nuclear" Option:** Use `--break-system-packages` to force installation or removal into the system/user python path.
```bash
# Install
pip install --break-system-packages fastapi uvicorn agno python-dotenv pydantic
# Uninstall (e.g., removing CUDA bloat from a no-GPU VM)
pip uninstall -y --break-system-packages nvidia-cublas nvidia-cuda-runtime torch
```

### 4. Eliminating Dependency "Bloat"
Avoid `torch`, `cuda`, and `triton` in lightness-critical environments (like low-RAM Render/VM plans).
- Remove `llama-index` if using a purely symbolic or API-based KG.
- Purge `uv.lock` and `poetry.lock` to force a fresh, lean resolution.
```bash
rm -f uv.lock
```

### 5. Fail-Safe Execution
Avoid `uv run` if the environment state is suspect. Use direct module execution.
```bash
python3 -m uvicorn app_module:app --host 0.0.0.0 --port 8000
```

## Pitfalls
- **The `uv` Sync Loop:** `uv` may try to download huge wheels (like PyTorch) even if you've deleted the requirements, if the lock file still exists. **Always delete the lock file first.**
- **Line-Number Injection:** Some LLM tool outputs for `read_file` include line numbers. If these are written back to scripts/configs, the parser will crash.

## Verification
- Check port status via `curl -v` to the local endpoint.
- Verify library import: `python3 -c "import agno; print('Success')"`
