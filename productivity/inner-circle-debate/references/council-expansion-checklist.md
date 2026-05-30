# Council Expansion Checklist (2026-05-21 verified, 15-seat)

## 1. Create Profile

```bash
hermes profile create <name> --clone-from default
```

## 2. Configure Model

**Kimi-2.6 seats** (Fei-Fei, Andrew, Andrej, Musk, Jobs, Guido, Dijkstra):
```bash
<name> config set model.default kimi-k2.6
<name> config set model.provider kimi-coding-cn
<name> config set model.context_length 65536
<name> config set auxiliary.compression.context_length 65536
```

**DeepSeek flash seats** (Demi, Lisa, Sam, Jensen, Xuefeng):
```bash
<name> config set model.default deepseek-v4-flash
<name> config set model.provider deepseek
```

## 3. Fix Clone Artifacts

```bash
# Remove stale base_url from --clone-from
sed -i '/base_url:/d' ~/.hermes/profiles/<name>/config.yaml

# Fix custom_providers: must be list, not dict (causes startup error)
python3 -c "
import yaml
with open('~/.hermes/profiles/<name>/config.yaml') as f:
    cfg = yaml.safe_load(f)
if isinstance(cfg.get('custom_providers'), dict):
    cfg['custom_providers'] = []
    with open('~/.hermes/profiles/<name>/config.yaml', 'w') as f:
        yaml.dump(cfg, f)
"
```

## 4. Write SOUL.md

Rich persona with: identity, philosophy, role, communication style.
English for non-Chinese seats. Chinese for Chinese seats.
Backup to `council_profiles/<name>_SOUL.md` in the project repo.

## 5. Smoke Test

```bash
<name> chat -q "Who are you? One sentence."
```

## 6. Update Skill & Memory

- Patch inner-circle-debate roster (15 seats)
- Update memory council entry
- Push to hermes-skills repo

## 7. Backup SOUL.md

```bash
cp ~/.hermes/profiles/<name>/SOUL.md ~/projects/<project>/council_profiles/<name>_SOUL.md
```

## 15-Seat Roster (2026-05-21)

| Seat | Name | Code | Model | Lang |
|------|------|------|-------|------|
| CTO | Feng Ge | fengge | pro | CN |
| CVO | Elon Musk | musk | kimi-k2.6 | EN |
| CSA | Zhang Xuefeng | xuefeng | flash | CN |
| Arch | Linus Torvalds | linus | pro | EN |
| Eng | Zhang Xiaolong | xiaolong | pro | CN |
| CPO | Steve Jobs | steve | kimi-k2.6 | EN |
| CLA | Guido van Rossum | guido | kimi-k2.6 | EN |
| CSO | Edsger Dijkstra | dijkstra | kimi-k2.6 | EN |
| CIO | Jensen Huang | jensen | flash | EN |
| CAS | Fei-Fei Li | feifei | kimi-k2.6 | EN |
| CCT | Demi Guo | demi | flash | EN |
| CHO | Lisa Su | lisasu | flash | EN |
| CLO | Andrew Ng | andrew | kimi-k2.6 | EN |
| CRO | Andrej Karpathy | andrej | kimi-k2.6 | EN |
| CPSO | Sam Altman | sam | flash | EN |

## Profile Aliases

Profiles accessible via `~/.local/bin/<name>`. Use `<name> chat` or `hermes --profile <name>`.
