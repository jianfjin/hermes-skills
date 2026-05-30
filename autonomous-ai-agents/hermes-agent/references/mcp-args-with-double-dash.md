# MCP Server: --args with double-dash flags

When adding an MCP server whose command needs `--prefixed` arguments (e.g., `code-review-graph mcp --repo /path`), `hermes mcp add --args` cannot pass `--repo` because Hermes CLI interprets it as its own flag.

## Failure pattern

```bash
hermes mcp add code-review-graph --command=code-review-graph --args mcp --args --repo=/path
# → hermes: error: unrecognized arguments: --repo=/path
```

## Fix: edit config.yaml directly

Add the server first without the problematic args, then patch config.yaml:

```bash
hermes mcp add code-review-graph --command=code-review-graph --args mcp
# → 30 tools detected (accept all)
```

Then:
```bash
python3 -c "
import yaml
with open(expanduser('~/.hermes/config.yaml')) as f:
    c = yaml.safe_load(f)
c['mcp_servers']['code-review-graph']['args'] = ['mcp', '--repo', '/path/to/repo']
with open(expanduser('~/.hermes/config.yaml'), 'w') as f:
    yaml.dump(c, f, default_flow_style=False)
"
```

Restart gateway or `/reload-mcp` in session. No restart required — tools appear on next `/reload-mcp`.

## Verified

- Hermes CLI (2026-05-18)
- code-review-graph 2.3.3 with 30 tools including `get_review_context_tool`, `query_graph_tool`, `semantic_search_nodes_tool`
