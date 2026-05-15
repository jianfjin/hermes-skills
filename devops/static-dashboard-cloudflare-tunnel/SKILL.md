---
name: static-dashboard-cloudflare-tunnel
description: Deploy a static HTML dashboard from a remote VM to a user using Cloudflare Tunnel to bypass firewall rules.
category: devops
---

# Static Dashboard Deployment via Cloudflare Tunnel

A high-efficiency workflow for delivering a static UI/Dashboard (e.g., HTML/React/Streamlit) from a remote GCP/Linux VM to a user without modifying firewall rules or configuring static IPs.

## Trigger Conditions
- User wants to visualize a local file/app via a browser.
- The environment is a remote VM (GCP, AWS, Azure) with strict firewall/ingress rules.
- User prefers a "zero-config" or "no-auth" temporary access link over manual port forwarding or SSH tunneling.

## Implementation Steps

### 1. Prepare the Static Content
Ensure the dashboard is a single-file HTML or a directory of static assets. 
If creating from an LLM, use a professional CSS framework via CDN (e.g., Tailwind CSS) to avoid asset management overhead.

### 2. Set Up the Local Serve Layer
Run a lightweight HTTP server to expose the content on a local port (default: 8000).
```bash
mkdir -p ~/web_root
cp your_file.html ~/web_root/index.html
nohup python3 -m http.server 8000 --directory ~/web_root > server.log 2>&1 &
```

### 3. Establish the Tunnel
Install `cloudflared` and launch a temporary tunnel to map the local port to a public `.trycloudflare.com` URL.
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Start ephemeral tunnel
nohup cloudflared tunnel --url http://localhost:8000 > tunnel.log 2>&1 &
```

### 4. Extract and Deliver the URL
Parse the `tunnel.log` to retrieve the dynamically generated public URL.
```bash
grep -o "https://[^ ]*\.trycloudflare.com" tunnel.log | tail -n 1
```

## Pitfalls & Corrections
- **Port Conflicts**: If 8000 is occupied, change the server and tunnel port.
- **Zombies**: `nohup` processes persist. If updating the UI, restart the `http.server` or simply overwrite the `index.html` (Python's server picks up changes on refresh).
- **Tunnel Stability**: Ephemeral tunnels can occasionally time out; provided as a "temporary" solution.
- **Firewall**: This method completely bypasses GCP/AWS ingress rules because it creates an outgoing connection to Cloudflare.

## Verification
- The delivered URL should open the static page in a standard web browser.
- Sensitivity sliders and interactive JS elements must function without a persistent backend since the logic is embedded in the static HTML.
