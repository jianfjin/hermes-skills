---
name: static-dashboard-tunnel-deployment
description: Deploy a static HTML dashboard from a GCP VM to a public URL using Cloudflared and a lightweight Python server.
---

# Static Dashboard Deployment via Cloudflare Tunnel (GCP VM)

## Trigger
When the user wants to deploy a quick, high-impact visual dashboard (HTML/JS/CSS) from a GCP VM to a public URL without managing firewall rules or complex server setups.

## Workflow
1. **Project Structure**:
    - Create a dedicated web root (e.g., `~/web_root`).
    - Save the main entry point as `index.html` in that root.
2. **Serve Locally**:
    - Use a lightweight Python server: `nohup python3 -m http.server <PORT> --directory <DIR> > server.log 2>&1 &`.
    - Verify port status with `netstat -lnpt | grep <PORT>`.
3. **Tunneling with Cloudflared**:
    - **Binary Installation**: Avoid `.deb` packages if `sudo` is restricted; download the binary directly from GitHub releases and `chmod +x`.
    - **Tunnel Execution**: 
        - For ephemeral tunnels: `cloudflared tunnel --url http://localhost:<PORT>`.
        - For managed tunnels: Use the provided Tunnel ID or Token: `cloudflared tunnel run <TUNNEL_ID>`.
4. **Troubleshooting 502/404**:
    - `502 Bad Gateway`: The tunnel is working, but the local server is dead or on the wrong port. Force kill old processes via `fuser -k <PORT>/tcp` and restart.
    - `404 Not Found`: The server is running, but the path to `index.html` is incorrect or the file is missing from the served directory.

## Pitfalls
- **Sudo Restrictions**: Avoid `dpkg -i` in restricted VM environments; prefer standalone binaries.
- **Port Collision**: Always `pkill` or `fuser -k` old servers before starting a new one to avoid "Address already in use" errors.
- **Ghost Processes**: Use `netstat` to verify the server is actually in `LISTEN` state before assuming the tunnel is at fault.