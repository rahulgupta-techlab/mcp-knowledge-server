# MCP Knowledge Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that gives an
MCP client (a desktop AI assistant, an IDE agent, or your own agent) safe,
structured access to plant-operations data:

- **Tools**
  - `list_tables`: database schema discovery so the model can plan queries
  - `query_database`: read-only SQL over a SQLite database of machines and incidents
  - `search_docs`: keyword search over policy documents (maintenance, safety, escalation)
- **Resource**: `docs://{name}` returns the full text of a document
- **Prompt**: `incident_review(machine_id)` is a reusable workflow that tells the model which tools to chain and to ground every claim in tool output

The scenario is a small manufacturing plant, but the pattern is general:
**expose internal data to agents through narrow, validated tools instead of giving them raw access.**

## Guardrails

The tools assume the model may send bad input:

| Risk | Guard |
| --- | --- |
| Writes / schema changes | Only one `SELECT`/`WITH` statement; write and `PRAGMA` keywords rejected |
| Statement stacking | `;` inside the query is rejected |
| Huge result sets | Results capped at 100 rows |
| Path traversal on resources | Names restricted to `[A-Za-z0-9_-]`, resolved path must stay in `data/docs` |
| Bad input crashing the server | Validation errors are returned as MCP tool errors (`isError`), not exceptions |

## Project layout

```
src/
  tools.py        # pure tool logic + guardrails (no MCP dependency, unit-tested)
  server.py       # FastMCP wiring: tools, resource, prompt; stdio transport
  client_demo.py  # MCP client: spawns the server, lists tools, calls them
data/
  seed.sql        # machines + incidents tables
  docs/*.md       # policy documents
tests/
  test_tools.py   # guardrail and tool-logic tests
  test_server.py  # end-to-end tests through a real MCP ClientSession
```

## Run it

```bash
pip install -r requirements.txt
python -m pytest            # 16 tests
python -m src.client_demo   # starts the server over stdio and calls each tool
```

### Use it from an MCP client

```json
{
  "mcpServers": {
    "plant-knowledge": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/mcp-knowledge-server"
    }
  }
}
```

Add this entry to your MCP client's server configuration (most desktop and IDE clients use this format).

## Design notes

- Tool logic lives in `tools.py` with no MCP imports, so it can be tested and reused (for example behind a REST API) independently of the protocol layer.
- Tool docstrings are written for the model: they say *when* to call the tool (`list_tables` before writing SQL), not just what it does.
- The server tests use the SDK's in-memory transport, so they exercise real MCP serialization (tool discovery, calls, errors, resources, prompts) without spawning processes.

## License

MIT
