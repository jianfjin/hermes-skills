# Gateway Platform ImportError — Diagnostic Playbook

## Symptom
Hermes gateway (or a `/reset`) reports `ImportError` / `ModuleNotFoundError` for a messaging platform (e.g. WhatsApp) immediately on startup or session reset. The platform worked previously or was configured by copying an old config snippet.

## Root Causes (in order of likelihood)

1. **Stale `platform_toolsets` referencing a non-existent plugin**  
   `config.yaml` lists a plugin name under `platform_toolsets.<platform>` that is not installed/bundled. Hermes tries to import it at gateway startup and fails.
2. **Missing Python dependency** for a bundled platform adapter.  
   The adapter itself imports an optional package (e.g. `discord.py`, `python-telegram-bot`) that is not in the venv.
3. **Corrupt or incompatible plugin** in `plugins/platforms/`.  
   A third-party platform plugin has broken imports.

## Diagnostic Steps

### Step 1 — Identify the failing module
```bash
# Try importing the native platform adapter directly
python3 -c "import sys; sys.path.insert(0, '$HOME/.hermes/hermes-agent'); from gateway.platforms import <platform>; print('Native adapter OK')"
```
If this succeeds, the core adapter is fine; the problem is a **plugin/toolset config** issue (root cause #1 or #3).

### Step 2 — Check `platform_toolsets` in config
```bash
grep -n -A 2 "whatsapp:" ~/.hermes/config.yaml   # replace with your platform
```
Look under the `platform_toolsets:` section. If the platform lists a plugin name (e.g. `hermes-whatsapp`), verify it exists:
```bash
hermes plugins list | grep <plugin-name>
```
**If the plugin is missing** → remove the entry from `platform_toolsets.<platform>` in `config.yaml`.

### Step 3 — Check bundled vs plugin platforms
Native bundled adapters live at `gateway/platforms/<platform>.py`.  
Third-party plugin platforms live at `plugins/platforms/<name>/`.  
`platform_toolsets` should only reference **plugin names** when a plugin is actually installed.

### Step 4 — Verify optional dependencies
If the native adapter itself fails to import in Step 1:
```bash
hermes doctor
```
Look for missing optional packages in the "Required Packages" section. Install whatever is flagged.

## Fixes

| Cause | Fix |
|-------|-----|
| Stale `platform_toolsets` plugin ref | `hermes config edit` → delete the `- hermes-<platform>` line under that platform → `hermes gateway restart` |
| Missing optional dep | `pip install <package>` inside the Hermes venv, or follow `hermes doctor` guidance |
| Broken third-party plugin | Remove or upgrade the plugin directory from `plugins/platforms/` |

## Verification
After any config change:
```bash
hermes gateway restart
# Then check logs
tail -20 ~/.hermes/logs/gateway.log
```

## Note on `/reset`
`/reset` starts a **new conversation session** but does **not** reload gateway-level config or re-import platform modules. A config-level ImportError will persist across `/reset` until the config is fixed and the gateway process is restarted.
