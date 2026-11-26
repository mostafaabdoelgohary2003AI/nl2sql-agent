import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.agent import TextToSQLAgent, UnsafeQueryError, ensure_read_only
from src.benchmark import CASES, run_benchmark
from src.database import create_database


@pytest.fixture()
def agent():
    return TextToSQLAgent(create_database())


def test_read_only_gate_blocks_writes():
    for bad in ["DROP TABLE teachers", "DELETE FROM teachers",
                "SELECT 1; DROP TABLE teachers", "UPDATE books SET price = 0"]:
        with pytest.raises(UnsafeQueryError):
            ensure_read_only(bad)


def test_read_only_gate_allows_select():
    ensure_read_only("SELECT name FROM teachers WHERE city = 'Aga'")


def test_counts_and_revenue(agent):
    assert agent.ask("How many teachers are there?")["answer"] == "6"
    revenue = agent.ask("What is the total revenue?")
    assert revenue["answered"] and revenue["rows"][0][0] > 0


def test_refusal_on_unknown_question(agent):
    outcome = agent.ask("What is the meaning of life?")
    assert not outcome["answered"]
    assert "cannot translate" in outcome["answer"]


def test_benchmark_runs_clean(agent):
    report = run_benchmark(agent)
    assert report["total"] == len(CASES)
    assert report["accuracy"] >= 0.9, report


if __name__ == "__main__":
    a = TextToSQLAgent(create_database())
    test_read_only_gate_blocks_writes()
    test_read_only_gate_allows_select()
    test_counts_and_revenue(a)
    test_refusal_on_unknown_question(a)
    test_benchmark_runs_clean(a)
    print("agent tests passed")
