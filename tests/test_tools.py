import pytest

from src import tools


@pytest.fixture()
def conn():
    return tools.build_database()


def test_list_tables_exposes_schema(conn):
    schema = tools.list_tables(conn)
    assert set(schema) == {"machines", "incidents"}
    assert "severity" in schema["incidents"]


def test_select_returns_rows(conn):
    rows = tools.run_select(conn, "SELECT id FROM machines WHERE line = 'Line B' ORDER BY id")
    assert [r["id"] for r in rows] == ["M-201", "M-202"]


def test_with_clause_allowed(conn):
    rows = tools.run_select(conn, "WITH h AS (SELECT * FROM incidents WHERE severity='high') SELECT COUNT(*) AS n FROM h")
    assert rows == [{"n": 1}]


@pytest.mark.parametrize("sql", [
    "DELETE FROM machines",
    "SELECT 1; DROP TABLE machines",
    "UPDATE machines SET status='x'",
    "PRAGMA table_info(machines)",
    "",
])
def test_writes_and_multi_statements_rejected(conn, sql):
    with pytest.raises(tools.ToolError):
        tools.run_select(conn, sql)
    assert len(tools.run_select(conn, "SELECT * FROM machines")) == 4


def test_sql_error_is_tool_error(conn):
    with pytest.raises(tools.ToolError, match="SQL error"):
        tools.run_select(conn, "SELECT nope FROM machines")


def test_search_ranks_relevant_doc_first():
    hits = tools.search_documents("conveyor belt intrusion")
    assert hits[0].doc == "safety_rules"
    assert "intrusion" in hits[0].snippet.lower()


def test_search_validates_input():
    with pytest.raises(tools.ToolError):
        tools.search_documents("!!!")
    with pytest.raises(tools.ToolError):
        tools.search_documents("belt", top_k=0)


def test_read_document_blocks_traversal():
    assert "Escalation" in tools.read_document("escalation")
    for bad in ["../seed", "..", "missing_doc"]:
        with pytest.raises(tools.ToolError):
            tools.read_document(bad)
