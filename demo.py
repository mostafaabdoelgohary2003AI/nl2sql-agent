"""Build the sample business database and run the NL->SQL benchmark.

Usage: python demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent import TextToSQLAgent
from src.benchmark import run_benchmark
from src.database import create_database


def main() -> None:
    agent = TextToSQLAgent(create_database())
    report = run_benchmark(agent)
    print(f"nl2sql benchmark: {report['correct']}/{report['total']} correct "
          f"(accuracy {report['accuracy']:.0%})")
    for item in report["results"]:
        mark = "PASS" if item["passed"] else "FAIL"
        print(f"  [{mark}] {item['question']}")
        if item["detail"] != "ok":
            print(f"         {item['detail']}")
    print("\nsample interaction:")
    for question in ["What is the total revenue from Mansoura?",
                     "Which teacher has the most books?",
                     "Drop the teachers table"]:
        outcome = agent.ask(question)
        print(f"  Q: {question}")
        print(f"     sql: {outcome['sql']}")
        print(f"     ->  {outcome['answer']}")


if __name__ == "__main__":
    main()
