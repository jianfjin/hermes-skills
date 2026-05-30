# VM Disk Space Recovery

For small VMs (30G or less), disk fills up from caches. This is the quick-recovery playbook.

## Quick Wins (safe to delete)

```bash
# pip cache — 600M+ typical
rm -rf ~/.cache/pip

# uv cache — 1.2G+ if using uv
rm -rf ~/.cache/uv

# npm cache
npm cache clean --force

# Python bytecode caches (scattered, small individually, adds up)
find ~/projects -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find ~/projects -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Old /tmp files
find /tmp -maxdepth 1 -type f -mtime +1 -delete
```

## Check Before Deleting

```bash
df -h /                          # how bad is it?
du -sh ~/.cache/* 2>/dev/null | sort -rh | head -10   # cache hogs
du -sh ~/projects/*/.venv 2>/dev/null                  # venv sizes
du -sh ~/.hermes/state.db                              # session db (can VACUUM)
```

## Hermes state.db VACUUM

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/state.db')
conn.execute('VACUUM')
conn.close()
"
```

## What NOT to delete

- `~/.hermes/` — configs, sessions, skills
- `~/.cache/chroma` — chromadb test/production data
- `~/.skillclaw/` — SkillClaw config and skills
- Project `.venv/` directories — needed to run code
- `/tmp/hermes-migration-*.tar.gz` — migration packages you may need

## After cleanup

```bash
df -h /    # verify free space
```
