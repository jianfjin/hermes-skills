---
name: cloudflare-tunnel-static-deploy
description: Deploy a static HTML dashboard from a GCP VM to a public domain via Cloudflare Tunnel without root/sudo requirements.
---

# Cloudflare Tunnel Static Site Deployment via GCP VM

This skill outlines the workflow for deploying a static HTML dashboard from a Google Cloud Platform (GCP) VM to a public domain using a Cloudflare Tunnel.

## Trigger Conditions
- Need to expose a local port (e.g., 8080) on a GCP VM to a public URL with SSL.
- Avoid opening GCP firewall ports manually.
- Requirement for a persistent domain (e.g., audit.edmf.nl).

## Implementation Steps

1. **Prepare Static Content**
   - Create a dedicated web root: `mkdir -p ~/web_root`
   - Place the HTML file as `index.html` in the root.

2. **Start Local HTTP Server**
   - Use Python's built-in server for lightweight hosting:
     `nohup python3 -m http.server 8080 --directory ~/web_root > server.log 2>&1 &`

3. **Install Cloudflared (Binary Mode)**
   - To avoid `sudo` permission issues in restricted VM environments:
     - Download binary: `curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared`
     - Make executable: `chmod +x cloudflared`

4. **Establish Tunnel**
   - **Option A (Ephemeral/Temp):** `nohup ./cloudflared tunnel --url http://localhost:8080 > tunnel.log 2>&1 &`
   - **Option B (Permanent/Managed):** Use the tunnel token from Cloudflare Dashboard:
     `nohup ./cloudflared tunnel run --token <YOUR_TOKEN> > tunnel.log 2>&1 &`

5. **Configuration on Cloudflare Dashboard**
   - Go to Tunnels $\rightarrow$ [Your Tunnel] $\rightarrow$ Public Hostname.
   - Map `your-domain.com` to `http://localhost:8080`.

## Pitfalls & Troubleshooting
- **502 Bad Gateway**: Usually means the tunnel is connected but the local server on the target port is not running or is crashing. Check `server.log`.
- **Sudo Permission Errors**: Avoid `.deb` packages in restricted environments; always use the direct binary download.
- **Port Collision**: Use `pkill -f "python3 -m http.server"` and `pkill -f "cloudflared"` before restarting.
- **Zombies**: In some VM environments, processes may hang; check for active listeners via `netstat -tulpn`.

## Verification
- Check if the process is listening: `curl -I http://localhost:8080`
- Access the public URL and check for SSL certification and page load.
