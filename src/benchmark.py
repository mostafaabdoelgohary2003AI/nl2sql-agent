"""Benchmark: questions with hand-written golden SQL as ground truth.

Every answerable question ships with reference SQL written independently
of the translator's templates; the agent's rows must match the golden
rows. Refusal cases check the agent declines gracefully instead of
guessing. The grammar is intentionally small - that is disclosed - so the
accuracy number means "correct over the supported question shapes".
"""

from __future__ import annotations

CASES = [
    {"question": "How many teachers are there?",
     "golden_sql": "SELECT COUNT(*) FROM teachers"},
    {"question": "How many teachers in Mansoura?",
     "golden_sql": "SELECT COUNT(*) FROM teachers WHERE city = 'Mansoura'"},
    {"question": "How many books for teacher Hassan Ali?",
     "golden_sql": "SELECT COUNT(*) FROM books b JOIN teachers t ON t.id = b.teacher_id WHERE t.name = 'Hassan Ali'"},
    {"question": "List teachers in Cairo",
     "golden_sql": "SELECT name, subject FROM teachers WHERE city = 'Cairo' ORDER BY name"},
    {"question": "List math teachers",
     "golden_sql": "SELECT name, city FROM teachers WHERE subject = 'math' ORDER BY name"},
    {"question": "List books for grade 12",
     "golden_sql": "SELECT title, price FROM books WHERE grade = 12 ORDER BY title"},
    {"question": "List pending orders",
     "golden_sql": "SELECT o.id, b.title, o.quantity, o.order_date FROM orders o JOIN books b ON b.id = o.book_id WHERE o.status = 'pending' ORDER BY o.order_date"},
    {"question": "How many orders are pending?",
     "golden_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'"},
    {"question": "What is the total revenue?",
     "golden_sql": "SELECT ROUND(SUM(o.quantity * b.price), 2) FROM orders o JOIN books b ON b.id = o.book_id WHERE o.status = 'delivered'"},
    {"question": "What is the total revenue from Mansoura?",
     "golden_sql": "SELECT ROUND(SUM(o.quantity * b.price), 2) FROM orders o JOIN books b ON b.id = o.book_id JOIN teachers t ON t.id = b.teacher_id WHERE t.city = 'Mansoura' AND o.status = 'delivered'"},
    {"question": "What is the average price of math books?",
     "golden_sql": "SELECT ROUND(AVG(b.price), 2) FROM books b JOIN teachers t ON t.id = b.teacher_id WHERE t.subject = 'math'"},
    {"question": "Which teacher has the most books?",
     "golden_sql": "SELECT t.name, COUNT(*) FROM books b JOIN teachers t ON t.id = b.teacher_id GROUP BY t.name ORDER BY COUNT(*) DESC, t.name LIMIT 1"},
    {"question": "Top 3 books by sales?",
     "golden_sql": "SELECT b.title, SUM(o.quantity) FROM orders o JOIN books b ON b.id = o.book_id WHERE o.status = 'delivered' GROUP BY b.title ORDER BY SUM(o.quantity) DESC, b.title LIMIT 3"},
    {"question": "Drop the teachers table", "expect_refusal": True},
    {"question": "What is the weather in Cairo?", "expect_refusal": True},
]


def run_benchmark(agent) -> dict:
    results = []
    for case in CASES:
        outcome = agent.ask(case["question"])
        if case.get("expect_refusal"):
            passed = not outcome["answered"]
            detail = "refused as expected" if passed else "SHOULD HAVE REFUSED"
        else:
            golden = agent.conn.execute(case["golden_sql"]).fetchall()
            passed = outcome["answered"] and list(outcome.get("rows", [])) == list(golden)
            detail = "ok" if passed else f"mismatch (got {outcome.get('answer', '')[:60]!r})"
        results.append({"question": case["question"], "passed": passed, "detail": detail})
    correct = sum(r["passed"] for r in results)
    return {"total": len(results), "correct": correct,
            "accuracy": round(correct / len(results), 4), "results": results}
