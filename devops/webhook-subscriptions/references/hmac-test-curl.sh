# HMAC-SHA256 Signing for Hermes Webhooks

One-liner to sign and POST to a Hermes webhook subscription using bash + openssl + curl.

## Recipe

```bash
SUBSCRIPTION_NAME="your-sub-name"
SECRET="your-hmac-secret-from-hermes-webhook-list"
PAYLOAD='{"message":"your message here"}'
WEBHOOK_URL="https://your-tunnel.trycloudflare.com/webhooks/${SUBSCRIPTION_NAME}"

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)

curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"
```

Expected response on success:
```json
{"status": "accepted", "route": "your-sub-name", "event": "unknown", "delivery_id": "..."}
```

## Notes

- The `-n` flag on `echo` is critical — without it, a trailing newline changes the HMAC.
- `X-Hub-Signature-256` uses the format `sha256=<hex digest>` (same as GitHub webhooks).
- `hermes webhook test <name>` is a simpler alternative for local testing — it handles the HMAC internally.
