"""The agent: translate -> safety check -> dry-run -> execute -> answer.

Safety is structural, not a polite prompt: only single SELECT statements
ever reach sqlite, every statement is EXPLAIN-checked first, and results
are capped. The optional LLM mode lets a model write the SQL, but it goes
through the exact same gate - a model proposal is a suggestion, never
trusted SQL.
"""

from __future__ import annotations

import re
import sqlite3

from .database import SCHEMA_DESCRIPTION
from .translator import translate

_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", re.I)
MAX_ROWS = 50


class UnsafeQueryError(ValueError):
    pass


def ensure_read_only(sql: str) -> None:
    """Reject anything that is not one plain SELECT."""
    statement = sql.strip().rstrip(";")
    if ";" in statement:
        raise UnsafeQueryError("multiple statements are not allowed")
    if not statement.lower().startswith("select"):
        raise UnsafeQueryError("only SELECT statements are allowed")
    if _FORBIDDEN.search(statement):
        raise UnsafeQueryError("write/DDL keywords are not allowed")


class TextToSQLAgent:
    def __init__(self, conn: sqlite3.Connection, llm=None, use_rules: bool = True) -> None:
        self.use_rules = use_rules
        self.conn = conn
        self.llm = llm  # optional OpenAI-compatible client with .complete()
        names = conn.execute("SELECT name FROM teachers").fetchall()
        self.teacher_names = [n for (n,) in names]

    def _propose_sql(self, question: str) -> tuple[str | None, str]:
        sql = translate(question, self.teacher_names) if self.use_rules else None
        if sql is not None:
            return sql, "rules"
        if self.llm is not None:
            proposal = self.llm.complete(
                "You translate questions into a single SQLite SELECT over this schema:\n"
                + SCHEMA_DESCRIPTION
                + "\nReply with the SQL only, no explanation.",
                question,
            )
            return proposal.strip().strip("`"), "llm"
        return None, "none"

    def ask(self, question: str) -> dict:
        sql, source = self._propose_sql(question)
        if sql is None:
            return {
                "question": question,
                "answered": False,
                "answer": "I cannot translate this question yet - the offline grammar "
                          "covers counts, lists, revenue, averages and rankings over "
                          "teachers/books/orders.",
                "sql": None,
                "source": source,
            }
        try:
            ensure_read_only(sql)
            self.conn.execute(f"EXPLAIN QUERY PLAN {sql}")  # dry-run before executing
            rows = self.conn.execute(sql).fetchmany(MAX_ROWS)
        except (UnsafeQueryError, sqlite3.Error) as exc:
            return {
                "question": question,
                "answered": False,
                "answer": f"refused: {exc}",
                "sql": sql,
                "source": source,
            }
        return {
            "question": question,
            "answered": True,
            "answer": self._format(rows),
            "sql": sql,
            "source": source,
            "rows": rows,
        }

    @staticmethod
    def _format(rows: list[tuple]) -> str:
        if not rows:
            return "no matching rows"
        if len(rows) == 1 and len(rows[0]) == 1:
            return str(rows[0][0])
        return "; ".join(", ".join(str(value) for value in row) for row in rows)
