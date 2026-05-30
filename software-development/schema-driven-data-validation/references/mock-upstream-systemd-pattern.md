# Mock Upstream REST Services via systemd

When developing a system that consumes upstream REST services (WP2/WP3/WP8),
run the mocks as `aiohttp.web` apps under **systemd user services** for
persistence across reboots and automatic crash recovery.

## Architecture

```
~/.config/systemd/user/scailed-mocks.service
└── ExecStart: services/mock/run_all_mocks.sh start
    ├── wp2_stakeholders.py :8102  (stakeholder taxonomy, list of dicts)
    ├── wp3_roadmap.py      :8103  (roadmap graph, 1K nodes + 1.8K edges)
    └── wp8_rules.py        :8108  (compliance rules, 1K+ rules as JSON)
```

Each mock is a standalone Python `aiohttp.web` application (<80 lines) that:
- Reads fixtures from `services/mock/fixtures/*.json`
- Serves `GET /health` (liveness) and `GET /api/v1/<resource>` (data)

## Unified Runner Script

```bash
services/mock/run_all_mocks.sh {start|stop|restart|status}
```

- Launches 3 Python processes as subprocesses of a bash parent
- Writes PIDs to `/tmp/scailed-mocks.pid`
- Trap handler kills all children on SIGINT/SIGTERM
- Supports status check (probes /health on each port)

## Systemd User Service

```ini
[Unit]
Description=Mock Services (WP2/WP3/WP8)
After=network.target

[Service]
Type=exec
ExecStart=%h/projects/<project>/services/mock/run_all_mocks.sh start
ExecStop=%h/projects/<project>/services/mock/run_all_mocks.sh stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable: `systemctl --user enable --now scailed-mocks.service`

## Consuming from the Application

Use `UpstreamClient` (aiohttp-based) with `localhost` URLs:

```python
client = UpstreamClient(
    wp2_url="http://localhost:8102/api/v1",
    wp3_url="http://localhost:8103/api/v1",
    wp8_url="http://localhost:8108/api/v1",
)
asyncio.run(client.startup())
```

## Pitfalls

- **Port conflicts**: If Docker Compose also maps these ports, systemd will
  fail to bind. Stop the containers or change ports.
- **Temp wrapper scripts**: Avoid placing runner scripts in `/tmp` — they get
  cleaned on reboot. Use a permanent location under the project directory.
- **python3 -c inline**: Embedding the Python runner in a bash `$(python3 -c "...")`
  makes debugging impossible. Write a proper wrapper script that imports the
  mock module with `sys.path.insert()` and calls `web.run_app()`.
