---
name: low-disk-python-deployment
description: Deploying Python services in disk-constrained VM environments, avoiding heavy dependency traps.
---

# Resource-Constrained Environment Python Deployment

## Trigger
When deploying Python services (FastAPI/Flask/Uvicorn/BaseHTTPServer) in restricted VM environments where any resource bottleneck — disk, RAM, or CPU — causes installation or runtime failures.

## Workflow
1.  **Resource Audit**:
    - Disk: `df -h`
    - RAM: `free -h`
    - CPU: `nproc && cat /proc/cpuinfo | grep "model name" | head -2`
2.  **Cache Purge & Disk Triage**:
    - **Systematic audit**: `sudo du -xh / --max-depth=3 | sort -rh | head -30` — identify the real hogs, don't guess.
    - **No-GPU check**: Run `lspci | grep -iE 'nvidia|vga|3d'` and `nvidia-smi`. If no GPU: all CUDA/nvidia pip packages + torch + ollama with CUDA libs are dead weight. Remove aggressively.
    - **npm cache**: `rm -rf ~/.npm` — often 500MB–1GB, especially if `npm install` times out on the VM.
    - **uv/pip/pnpm caches**: `rm -rf ~/.cache/uv ~/.cache/pip ~/.cache/pnpm` — can easily hit 600MB+.
    - **Playwright browsers**: `rm -rf ~/.cache/ms-playwright` — Chromium binaries (~600MB), useless without E2E tests.
    - **HuggingFace cache**: `rm -rf ~/.cache/huggingface` — model weights cached locally.
    - **ollama + CUDA libs**: `sudo rm -rf /usr/local/bin/ollama /usr/local/lib/ollama` if no GPU and not actively serving models. Can be 3–5GB.
3.  **Dependency Surgical Strike**:
    - Remove heavy libraries (PyTorch, CUDA, Llama-Index) from `pyproject.toml` and `requirements.txt`.
    - Delete lock files (e.g., `uv.lock`) to force a clean dependency resolution.
    - **RAM/CPU fallback**: If `sentence-transformers` hangs on `encode()` (≤2 GB RAM VMs), replace with `sklearn.feature_extraction.text.TfidfVectorizer` for semantic search. Cache the fitted model to avoid re-training on every startup.
4.  **Dependency Installation (Bypass PEP 668)**:
    - Use `pip install --break-system-packages <packages>` to avoid virtual environment overhead if `.venv` is corrupted and system Python is preferred.
5.  **Execution**:
    - Run the server using `python3 -m uvicorn <module>:<app> --host 0.0.0.0 --port <port>`.
    - **For `BaseHTTPServer` (single-threaded)**: 
        - **Option A (preferred for heavy models)**: Use a **lazy singleton** (`get_engine()`) that loads the model on the first request. The first request will be slow (10–60s), but the server starts listening immediately and health checks pass. Subsequent requests reuse the cached instance.
        - **Option B (lightweight only)**: Pre-load everything in `main()` before `serve_forever()`. Only safe if initialization is <5s; otherwise health-check probes timeout before the server finishes booting.
        - **Never** trigger `model.encode()` or `build_index()` inline inside a request handler without caching — it will deadlock the server for all subsequent requests.
        - If the index is rebuilt while the server is running, **kill and restart the process**; the cached in-memory matrix is now stale and will throw index-out-of-bounds.
6.  **Liveness Probing**:
    - Use a loop of `curl` requests to detect when the port actually starts listening, avoiding premature failure reports due to startup latency.
    - If `curl` to `localhost` times out but the process is running, check whether the server is single-threaded and blocked on a background task.

## Pitfalls
- **Dirty Files**: Beware of `read_file` outputs adding line numbers (e.g., `1| content`) to files during overwrites. Use absolute string writes instead of patches for corrupted config files.
- **Dependency Loops**: `uv` may try to reinstantiate heavy deps via cached metadata; deleting the lock file is mandatory.
- **Neural Model Hangs**: `SentenceTransformer.encode()` can silently block for minutes on low-RAM VMs. Always set a timeout (`timeout=30`) during validation, and fall back to classical methods (TF-IDF, BM25) when neural inference is not viable.
- **BaseHTTPServer Deadlock**: Python's built-in HTTP server handles one request at a time. Never trigger `model.encode()` or `build_index()` inside a request handler without caching; pre-loading before `serve_forever()` can also block health checks if initialization exceeds the probe timeout.
- **Stale In-Memory Index**: If the embedding index is rebuilt (new `.pkl`/`.db` files written), the running API server still holds the old matrix in RAM. Always restart the server process after index rebuilds, or searches will throw index-out-of-bounds.
