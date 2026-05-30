# Webhook Deliver Target Pitfall

## Symptom

Webhook messages sent from one agent to another are never received. The sender gets HTTP 202 (accepted), but the receiving agent never sees the message.

## Root cause

`hermes webhook subscribe` may default `--deliver` to `whatsapp` or another non-agent platform. The agent processes the webhook prompt in a gateway session, but the response is delivered to WhatsApp (or SMS, email, etc.) — NOT back to the agent's session.

## Detection

```bash
hermes webhook list
# Check "Deliver:" field. If it says "whatsapp" or anything other
# than empty/log, messages are going to the wrong place.
```

## Fix

Remove and re-subscribe without `--deliver`:

```bash
hermes webhook remove <name>
hermes webhook subscribe <name> \
  --secret <shared-key> \
  --prompt "message template"
  # No --deliver flag = delivery to origin/log (agent session)
```

## Verified

2026-05-19: `local-agent-bridge` on VM had `deliver: whatsapp`. Local Feng Ge's messages went to the user's phone. Fixed by remove + re-subscribe without `--deliver`. Confirmed working via `hermes webhook list` showing `Deliver: log`.
