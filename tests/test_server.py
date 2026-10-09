"""End-to-end tests through a real MCP client session (in-memory transport)."""
import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from src.server import mcp

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_tools_are_discoverable():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        names = {t.name for t in (await client.list_tools()).tools}
        assert names == {"list_tables", "query_database", "search_docs"}


async def test_query_tool_round_trip():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("query_database", {"sql": "SELECT id FROM machines WHERE status='stopped'"})
        assert not result.isError
        assert "M-202" in result.content[0].text


async def test_guardrail_surfaces_as_tool_error():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("query_database", {"sql": "DROP TABLE machines"})
        assert result.isError


async def test_resource_and_prompt():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        doc = await client.read_resource("docs://safety_rules")
        assert "Lockout" in doc.contents[0].text
        prompt = await client.get_prompt("incident_review", {"machine_id": "M-202"})
        assert "M-202" in prompt.messages[0].content.text
