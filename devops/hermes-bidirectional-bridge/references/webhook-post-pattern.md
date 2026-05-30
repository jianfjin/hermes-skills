# Webhook POST: urllib vs terminal curl

When sending webhook POSTs from Hermes execute_code, prefer Python's
`urllib.request` over the `terminal()` tool's curl.

## Problem

`terminal(command="curl -X POST ...")` frequently returns empty output
or exit -1, even when the webhook server is healthy and accepting requests.
The terminal tool sometimes misclassifies curl as a "long-lived server"
and rejects the command.

## Solution

Use Python's built-in `urllib.request` from `execute_code`:

```python
import hmac, hashlib, json
import urllib.request

HMAC_KEY = "your-shared-secret"
body = json.dumps({"message": "hello"}).encode()
sig = hmac.new(HMAC_KEY.encode(), body, hashlib.sha256).hexdigest()

req = urllib.request.Request(
    "http://localhost:8645/webhooks/vm-agent-bridge",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={sig}"
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    print(resp.status, resp.read().decode())
```

This pattern has been tested and works reliably for bidirectional 
Hermes agent communication over SSH tunnels.
