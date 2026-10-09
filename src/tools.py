"""Tool implementations, kept free of MCP so they can be unit-tested directly.

Two kinds of tools are exposed:
- read-only SQL over a small plant-operations SQLite database
- keyword search over a folder of markdown documents
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_ROWS = 100

_WRITE_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


class ToolError(ValueError):
    """Raised for invalid tool input; surfaced to the client as a tool error."""


def build_database(path: Path | str = ":memory:", seed_file: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite database from the seed script and return a connection."""
    seed_file = seed_file or DATA_DIR / "seed.sql"
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(seed_file.read_text(encoding="utf-8"))
    return conn


def list_tables(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Return {table_name: [column, ...]} so a model can plan its queries."""
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {t: [c[1] for c in conn.execute(f"PRAGMA table_info({t})")] for t in tables}


def run_select(conn: sqlite3.Connection, sql: str) -> list[dict]:
    """Execute a single read-only SELECT statement and return rows as dicts.

    Guardrails: one statement only, must start with SELECT/WITH, no write
    keywords, and results are capped at MAX_ROWS.
    """
    statement = sql.strip().rstrip(";").strip()
    if not statement:
        raise ToolError("Query is empty.")
    if ";" in statement:
        raise ToolError("Only a single statement is allowed.")
    if not re.match(r"^(select|with)\b", statement, re.IGNORECASE):
        raise ToolError("Only SELECT queries are allowed.")
    if _WRITE_KEYWORDS.search(statement):
        raise ToolError("Query contains a write or schema keyword.")
    try:
        cursor = conn.execute(statement)
    except sqlite3.Error as exc:
        raise ToolError(f"SQL error: {exc}") from exc
    return [dict(row) for row in cursor.fetchmany(MAX_ROWS)]


@dataclass
class DocHit:
    doc: str
    score: int
    snippet: str


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def search_documents(query: str, docs_dir: Path | None = None, top_k: int = 3) -> list[DocHit]:
    """Rank markdown documents by query-term overlap and return the best snippets."""
    docs_dir = docs_dir or DATA_DIR / "docs"
    terms = set(_tokens(query))
    if not terms:
        raise ToolError("Query has no searchable terms.")
    if not 1 <= top_k <= 10:
        raise ToolError("top_k must be between 1 and 10.")

    hits: list[DocHit] = []
    for path in sorted(docs_dir.glob("*.md")):
        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        scored = [(sum(t in terms for t in _tokens(line)), line) for line in lines]
        total = sum(s for s, _ in scored)
        if total:
            best = max(scored, key=lambda x: x[0])[1]
            hits.append(DocHit(doc=path.stem, score=total, snippet=best))
    hits.sort(key=lambda h: (-h.score, h.doc))
    return hits[:top_k]


def read_document(name: str, docs_dir: Path | None = None) -> str:
    """Return the full text of one document; rejects path traversal."""
    docs_dir = (docs_dir or DATA_DIR / "docs").resolve()
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise ToolError("Invalid document name.")
    path = (docs_dir / f"{name}.md").resolve()
    if path.parent != docs_dir or not path.exists():
        raise ToolError(f"Unknown document: {name}")
    return path.read_text(encoding="utf-8")
