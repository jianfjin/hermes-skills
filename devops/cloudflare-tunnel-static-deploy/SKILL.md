---
name: cloudflare-tunnel-static-deploy
description: Expose any local HTTP service (static site, webhook API, dashboard) from a cloud VM to a public URL via Cloudflare Tunnel, no firewall changes needed.
---

# Cloudflare Tunnel: Expose Local HTTP Services from Cloud VMs

Use Cloudflare Tunnel to expose any local HTTP port (static sites, Hermes webhook API, dashboards, REST endpoints) from a GCP/AWS/Azure VM to a public HTTPS URL. Bypasses cloud firewall restrictions without opening ports.

## Trigger Conditions
- Need to expose a local port (e.g., 8080, 8644) on a cloud VM to a public URL with SSL.
- Cloud firewall (GCP, AWS SG) blocks the port — don't want to open it manually.
- Quick ephemeral tunnel for testing, or persistent named tunnel for production.
- Works for: static HTML, Hermes webhook gateway, Python http.server, any HTTP service.

## Implementation Steps

### Ephemeral Tunnel (Quick, No Account Needed)

Best for one-off testing. URL changes on restart.

```bash
# Run in background (Hermes: use terminal(background=true))
cloudflared tunnel --url http://localhost:<PORT> --no-autoupdate 2>&1 | tee /tmp/cf_tunnel.log
```

Extract the `trycloudflare.com` URL from the log output. The tunnel auto-provisions SSL.

### Persistent Named Tunnel (Production)

For a stable domain that survives restarts (e.g., `webhook.your-domain.com`).

1. **Install cloudflared** — binary mode avoids sudo:
   ```bash
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/bin/cloudflared
   chmod +x ~/bin/cloudflared
   ```

2. **Authenticate**: `cloudflared tunnel login` (opens browser — run on local machine or use headless auth)

3. **Create tunnel**: `cloudflared tunnel create <name>`

4. **Configure** `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: /home/user/.cloudflared/<tunnel-id>.json
   ingress:
     - hostname: webhook.your-domain.com
       service: http://localhost:8644
     - service: http_status:404
   ```

5. **DNS**: In Cloudflare dashboard, add CNAME `<tunnel-id>.cfargotunnel.com` for your domain.

6. **Run**: `cloudflared tunnel run <name>` (or install as systemd service).

## Pitfalls & Troubleshooting
- **502 Bad Gateway**: Tunnel is connected but the local service on the target port is not running. Check `curl localhost:<PORT>/health`.
- **Sudo Permission Errors**: Avoid `.deb` packages in restricted VM environments; use the direct binary download.
- **Port Collision**: Use `pkill -f "cloudflared"` before restarting ephemeral tunnels.
- **Ephemeral URL changes on restart**: The `trycloudflare.com` subdomain is random each time. For stable URLs, use a named tunnel with your own domain.
- **No output in background mode**: Cloudflared logs to stderr. Use `2>&1 | tee` to capture, or check the timestamped trial URL in the first ~6 lines of stderr.
