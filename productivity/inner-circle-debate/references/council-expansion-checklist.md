# Council Expansion Checklist

Step-by-step for adding new seats to the Nine-Dragon Council.

## 1. Create Profile

```bash
hermes profile create <name> --clone-from default
```

## 2. Configure Model

```bash
# For kimi-k2.6 seats (must set context_length override):
<name> config set model.default kimi-k2.6
<name> config set model.provider kimi-coding-cn
<name> config set model.context_length 65536
<name> config set auxiliary.compression.context_length 65536

# For deepseek-v4-flash seats:
<name> config set model.default deepseek-v4-flash
<name> config set model.provider deepseek

# For deepseek-v4-pro seats:
<name> config set model.default deepseek-v4-pro
<name> config set model.provider deepseek
```

## 3. Remove Stale base_url

--clone-from copies the source profile's `model.base_url`. Delete the line from
`~/.hermes/profiles/<name>/config.yaml` if the provider changed:

```yaml
model:
  default: kimi-k2.6
  provider: kimi-coding-cn
  base_url: https://api.deepseek.com/v1  # ← DELETE THIS LINE
  context_length: 65536
```

## 4. Write SOUL.md

Key sections to include:
- Identity & background (birth, key achievements, current role)
- Core philosophy / beliefs (the "soul")
- Role in the council (specific responsibilities)
- Communication style (tone, quirks, catchphrases)
- Quotes to draw from
- Council output format tag: `[Name/ROLE]`

**Language rule:**
- Non-Chinese members (Musk, Jobs, Linus, Guido, Dijkstra, Jensen): English SOUL.md
- Chinese members (Xuefeng, Xiaolong): Chinese SOUL.md
- Feng Ge (default profile): no separate SOUL.md, persona in main session

## 5. Smoke Test

```bash
<name> chat -q "Who are you? One sentence."
```

Verify: correct persona voice, correct output format tag, correct language.

## 6. Update Skill

Patch `inner-circle-debate/SKILL.md`:
- Roster table (add row)
- Roles & Responsibilities table (add row)
- Setup section (add create/configure commands)
- Debate modes (update participant lists)

## 7. Update Memory

Add to the 9-seat roster memory entry with a compressed one-liner.

## 8. Backup SOUL.md

```bash
cp ~/.hermes/profiles/<name>/SOUL.md ~/projects/<project>/council_profiles/<name>_SOUL.md
```

## Profile Aliases

Profiles are accessible via wrapper scripts at `~/.local/bin/<name>`.
Use `<name> chat` or `hermes --profile <name>`.
