---
name: manim-troubleshooting
description: Guide for resolving common installation and runtime errors when using Manim Community Edition in AI agent environments.
tags: [manim, animation, python, troubleshooting, dependencies]
triggers:
  - "pangocairo >= 1.30.0 required"
  - "ValueError: operands could not be broadcast together"
  - "TypeError: Mobject.__init__() got an unexpected keyword argument"
---

# Manim Troubleshooting & Environment Setup

Rendering videos with Manim often fails due to the gap between Python dependencies and system-level C libraries.

## 1. The `pangocairo` Error
**Symptom:** `pip install manimpango` fails with `pangocairo >= 1.30.0 required`.
**Cause:** `manimpango` is a wrapper for Pango and Cairo. The Python package cannot be installed without the underlying system development headers.

**Solution:** Install system libraries first, then force-reinstall the python package.

- **Ubuntu/Debian/WSL:**
  `sudo apt-get update && sudo apt-get install -y libpango1.0-dev pkg-config libcairo2-dev`
- **macOS:**
  `brew install pango pkg-config cairo`
- **Fedora:**
  `sudo dnf install pango-devel cairo-devel pkgconfig`

**Critical Step:** After installing system libs, run:
`pip install --force-reinstall manimpango`

## 2. Common Runtime Crashes

### A. Array Broadcasting Errors (`ValueError`)
**Symptom:** `ValueError: operands could not be broadcast together with shapes (N,3) (2,)` when using `.shift()` or `.move_to()`.
**Cause:** Manim operates in 3D space $(x, y, z)$. Passing a 2D coordinate (e.g., `np.random.uniform(-3, 3, 2)`) to a shift function will cause a shape mismatch.
**Fix:** Always ensure coordinates are 3-element arrays.
- **Wrong:** `np.random.uniform(-3, 3, 2)`
- **Right:** `np.array([np.random.uniform(-3, 3), np.random.uniform(-3, 3), 0])`

### B. Unexpected Keyword Arguments (`TypeError`)
**Symptom:** `TypeError: Mobject.__init__() got an unexpected keyword argument 'italic'`
**Cause:** The `Text` object in Manim Community does not support `italic=True` directly in the constructor.
**Fix:** Use `Text("...", slant=TLex.ITALIC)` or apply a post-creation transformation if using specific fonts. For simple text, remove the `italic` argument and use `Text` normally.

## 3. Rendering Pipeline
When running in a headless environment:
1. Use `-qm` (Medium Quality) for testing to save time and compute.
2. Use `-qh` (High Quality) only for final delivery.
3. If the agent environment is restricted (no `sudo`), the user must install system deps locally before the agent can execute the Python script.
