# Joint Cross-Team Debate & Voting Pattern (2026-05-20 verified)

When VM council and local council must debate independently, then merge votes.

## Pattern

1. **Local team sends plan** → VM council audits it
2. **VM council produces rebuttal** with per-item vote table
3. **Joint re-vote** — all seats from both teams vote on each item
4. **Final resolution** with unanimous count

## Worked Example: DR Plan Debate (2026-05-20)

### Round 1: Local team proposes
- Local submits DR plan with streaming replication
- VM council (6 seats) audits: 3 blocking bugs found

### Round 2: VM council rebuts
- VM pushes audit report with vote table
- Local fixes bugs, resubmits

### Round 3: Joint vote
- VM 6 seats + local 9 seats = 15 total
- Vote on 4 items: replica(NO 15/0), cloud(YES 15/0), verify(YES 15/0), budget(YES 15/0)
- All items unanimous

## Vote Table Format

```markdown
| # | Item | VM Musk | VM Linus | ... | Local 峰哥 | Local ... | Result |
|---|------|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Item name | YES/NO | ... | ... | ... | ... | N/M |
```

## Communication Channels

- **Git push/pull** for formal documents
- **tmux send-keys** via SSH reverse tunnel for notifications
- **Webhook** (gateway) for background task triggers

## Pitfalls

- Cross-team debates take 2-3 rounds minimum. Budget time.
- Local agents can't "see" VM tmux sessions — use git for formal exchange
- kimi-2.6 agents timeout >120s during peak hours — launch them first
