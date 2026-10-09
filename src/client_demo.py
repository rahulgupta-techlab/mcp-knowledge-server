"""Minimal MCP client: launches the server over stdio, discovers its tools and calls them.

    python -m src.client_demo
"""
from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "src.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool(
                "query_database",
                {"sql": "SELECT machine_id, severity, summary FROM incidents WHERE severity='high'"},
            )
            print("High-severity incidents:", result.content[0].text)

            result = await session.call_tool("search_docs", {"query": "high severity escalation"})
            print("Policy search:", result.content[0].text)

            doc = await session.read_resource("docs://escalation")
            print("Resource docs://escalation:\n", doc.contents[0].text)


if __name__ == "__main__":
    asyncio.run(run())
