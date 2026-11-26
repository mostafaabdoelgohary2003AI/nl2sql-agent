"""Rule-based natural-language -> SQL translator.

Deterministic and inspectable: every supported question shape maps to one
SQL template over the sample schema. Unknown shapes return None, and the
agent refuses gracefully instead of guessing. The supported grammar is the
honest contract of the offline mode; the optional LLM mode handles the
long tail (see agent.py).
"""

from __future__ import annotations

import re

CITIES = ["mansoura", "cairo", "giza", "aga", "damietta"]
SUBJECTS = ["math", "science", "english", "arabic"]
STATUSES = ["pending", "delivered", "cancelled"]


def _find(words: str, options: list[str]) -> str | None:
    for option in options:
        if re.search(rf"(?<![a-z]){re.escape(option)}(?![a-z])", words):
            return option
    return None


def translate(question: str, teacher_names: list[str]) -> str | None:
    """Translate a supported question into SQL, else return None."""
    q = question.lower().strip().rstrip("?").strip()

    m = re.search(r"teacher ([a-z ]+)$", q)
    teacher = None
    if m:
        candidate = m.group(1).strip().title()
        teacher = next((n for n in teacher_names if n.lower() == m.group(1).strip()), candidate)

    city = _find(q, CITIES)
    subject = _find(q, SUBJECTS)
    status = _find(q, STATUSES)
    grade = None
    gm = re.search(r"grade (\d+)", q)
    if gm:
        grade = int(gm.group(1))
    top = None
    tm = re.search(r"top (\d+)", q)
    if tm:
        top = int(tm.group(1))

    # ---- count patterns ----
    if q in {"how many teachers", "how many teachers are there"} or (q.startswith("how many teachers") and not (city or subject or teacher)):
        return "SELECT COUNT(*) AS teacher_count FROM teachers"
    if q.startswith("how many teachers") and city:
        return f"SELECT COUNT(*) AS teacher_count FROM teachers WHERE city = '{city.title()}'"
    if q.startswith("how many teachers") and subject:
        return f"SELECT COUNT(*) AS teacher_count FROM teachers WHERE subject = '{subject}'"
    if q.startswith("how many books") and teacher:
        return (
            "SELECT COUNT(*) AS book_count FROM books b JOIN teachers t ON t.id = b.teacher_id "
            f"WHERE t.name = '{teacher}'"
        )
    if q in {"how many books", "how many books are there"}:
        return "SELECT COUNT(*) AS book_count FROM books"
    if q.startswith("how many orders") and status:
        return f"SELECT COUNT(*) AS order_count FROM orders WHERE status = '{status}'"
    if q.startswith("how many orders"):
        return "SELECT COUNT(*) AS order_count FROM orders"

    # ---- list patterns ----
    sm = re.match(r"^list (\w+) teachers$", q)  # "list math teachers"
    if sm and sm.group(1) in SUBJECTS:
        return f"SELECT name, city FROM teachers WHERE subject = '{sm.group(1)}' ORDER BY name"
    if q.startswith("list teachers") and city:
        return f"SELECT name, subject FROM teachers WHERE city = '{city.title()}' ORDER BY name"
    if q.startswith("list teachers") and subject:
        return f"SELECT name, city FROM teachers WHERE subject = '{subject}' ORDER BY name"
    if q.startswith("list teachers"):
        return "SELECT name, subject, city FROM teachers ORDER BY name"
    if q.startswith("list books") and grade:
        return f"SELECT title, price FROM books WHERE grade = {grade} ORDER BY title"
    if q.startswith("list books") and subject:
        return (
            "SELECT b.title, b.price FROM books b JOIN teachers t ON t.id = b.teacher_id "
            f"WHERE t.subject = '{subject}' ORDER BY b.title"
        )
    if q.startswith("list pending orders") or (q.startswith("list orders") and status == "pending"):
        return (
            "SELECT o.id, b.title, o.quantity, o.order_date FROM orders o "
            "JOIN books b ON b.id = o.book_id WHERE o.status = 'pending' ORDER BY o.order_date"
        )

    # ---- aggregates ----
    if "total revenue" in q and city:
        return (
            "SELECT ROUND(SUM(o.quantity * b.price), 2) AS revenue FROM orders o "
            "JOIN books b ON b.id = o.book_id JOIN teachers t ON t.id = b.teacher_id "
            f"WHERE t.city = '{city.title()}' AND o.status = 'delivered'"
        )
    if "total revenue" in q and teacher:
        return (
            "SELECT ROUND(SUM(o.quantity * b.price), 2) AS revenue FROM orders o "
            "JOIN books b ON b.id = o.book_id JOIN teachers t ON t.id = b.teacher_id "
            f"WHERE t.name = '{teacher}' AND o.status = 'delivered'"
        )
    if "total revenue" in q:
        return (
            "SELECT ROUND(SUM(o.quantity * b.price), 2) AS revenue FROM orders o "
            "JOIN books b ON b.id = o.book_id WHERE o.status = 'delivered'"
        )
    if "average price" in q and subject:
        return (
            "SELECT ROUND(AVG(b.price), 2) AS avg_price FROM books b "
            f"JOIN teachers t ON t.id = b.teacher_id WHERE t.subject = '{subject}'"
        )
    if "average price" in q:
        return "SELECT ROUND(AVG(price), 2) AS avg_price FROM books"

    # ---- rankings ----
    if "which teacher has the most books" in q:
        return (
            "SELECT t.name, COUNT(*) AS book_count FROM books b "
            "JOIN teachers t ON t.id = b.teacher_id GROUP BY t.name "
            "ORDER BY book_count DESC, t.name LIMIT 1"
        )
    if top and "book" in q and ("sold" in q or "sales" in q or "ordered" in q or "best" in q):
        return (
            "SELECT b.title, SUM(o.quantity) AS sold FROM orders o "
            "JOIN books b ON b.id = o.book_id WHERE o.status = 'delivered' "
            f"GROUP BY b.title ORDER BY sold DESC, b.title LIMIT {top}"
        )
    return None
