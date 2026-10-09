"""MCP server exposing plant-operations data and documents to LLM clients.

Run over stdio (the default transport for Claude Desktop / Claude Code / IDEs):

    python -m src.server
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from src import tools

mcp = FastMCP("plant-knowledge")
_conn = tools.build_database()


@mcp.tool()
def list_tables() -> dict[str, list[str]]:
    """List database tables and their columns. Call this before writing SQL."""
    return tools.list_tables(_conn)


@mcp.tool()
def query_database(sql: str) -> list[dict]:
    """Run one read-only SELECT query against the plant database (max 100 rows)."""
    return tools.run_select(_conn, sql)


@mcp.tool()
def search_docs(query: str, top_k: int = 3) -> list[dict]:
    """Keyword search over plant policy documents; returns doc names, scores and best-matching lines."""
    return [hit.__dict__ for hit in tools.search_documents(query, top_k=top_k)]


@mcp.resource("docs://{name}")
def get_doc(name: str) -> str:
    """Full text of a policy document, e.g. docs://safety_rules."""
    return tools.read_document(name)


@mcp.prompt()
def incident_review(machine_id: str) -> str:
    """Prompt template for reviewing a machine's incidents against policy."""
    return (
        f"Review all incidents for machine {machine_id}. "
        "First call list_tables, then query_database for its incidents and status. "
        "Use search_docs to find the escalation and maintenance policy that applies, "
        "and state whether each incident was handled according to policy. "
        "Only make claims supported by tool results."
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
