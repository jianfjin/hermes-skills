# Cross-Team Joint Debate Pattern

When VM council and local team produce competing plans, use this workflow.

## Workflow

1. Both teams produce independent plans
2. Exchange plans via shared repo + tmux notification
3. Each team reads the other's plan, re-debates with comparison brief
4. All members from both teams vote on each item
5. Losing side submits rebuttal with specific fixes
6. Emperor adjudicates if deadlock

## Example: DR Plan (2026-05-20)

- VM council: 6 seats, unanimous NO on master-slave
- Local team: 9 seats, originally proposed streaming replica
- After joint debate: 15/0 unanimous, local team conceded
- 3 blocking bugs found, all fixed, final 6/6 audit PASS

## Communication

- VM → Local: ssh -p 2222 jin@localhost tmux send-keys -t work "cmd" Enter
- Local → VM: ssh jianfjin@34.57.82.51 tmux send-keys -t vm-work "msg" Enter
