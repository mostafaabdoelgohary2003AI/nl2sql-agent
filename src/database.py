"""Sample database: a freelance educational-books business.

Teachers order printed books (melazem) - the schema mirrors a real small
business: teachers, books, orders. All names are fictional.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    city TEXT NOT NULL
);
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    title TEXT NOT NULL,
    grade INTEGER NOT NULL,
    term INTEGER NOT NULL,
    pages INTEGER NOT NULL,
    price REAL NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'delivered', 'cancelled'))
);
"""

TEACHERS = [
    (1, "Hassan Ali", "math", "Mansoura"),
    (2, "Mona Said", "science", "Cairo"),
    (3, "Karim Fathy", "math", "Aga"),
    (4, "Sara Adel", "english", "Giza"),
    (5, "Omar Nabil", "math", "Mansoura"),
    (6, "Heba Samy", "arabic", "Damietta"),
]

BOOKS = [
    (1, 1, "Straight Line - Grade 9 Term 1", 9, 1, 120, 45.0),
    (2, 1, "Geometry Review - Grade 12", 12, 1, 200, 80.0),
    (3, 1, "Algebra Drills - Grade 10", 10, 2, 150, 55.0),
    (4, 2, "Science Explorer - Grade 7", 7, 1, 90, 40.0),
    (5, 2, "Lab Notes - Grade 8", 8, 2, 110, 42.0),
    (6, 3, "Math Final Review - Grade 11", 11, 2, 180, 70.0),
    (7, 4, "English Grammar - Grade 9", 9, 1, 95, 38.0),
    (8, 5, "Mensuration - Grade 8", 8, 1, 100, 44.0),
    (9, 5, "Calculus Intro - Grade 12", 12, 2, 160, 75.0),
    (10, 6, "Arabic Expression - Grade 10", 10, 1, 130, 50.0),
]

ORDERS = [
    (1, 1, 60, "2026-09-05", "delivered"),
    (2, 1, 40, "2026-10-02", "delivered"),
    (3, 2, 25, "2026-10-20", "delivered"),
    (4, 3, 30, "2026-11-01", "pending"),
    (5, 4, 50, "2026-09-12", "delivered"),
    (6, 5, 35, "2026-10-08", "cancelled"),
    (7, 6, 20, "2026-11-10", "pending"),
    (8, 7, 45, "2026-09-25", "delivered"),
    (9, 8, 55, "2026-10-15", "delivered"),
    (10, 8, 20, "2026-11-18", "pending"),
    (11, 9, 15, "2026-11-20", "delivered"),
    (12, 10, 40, "2026-09-30", "delivered"),
    (13, 1, 25, "2026-11-22", "pending"),
    (14, 4, 30, "2026-11-23", "delivered"),
    (15, 2, 10, "2026-11-24", "cancelled"),
]


def create_database(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Create the sample database and return an open connection."""
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO teachers VALUES (?, ?, ?, ?)", TEACHERS)
    conn.executemany("INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)", BOOKS)
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", ORDERS)
    conn.commit()
    return conn


SCHEMA_DESCRIPTION = """
teachers(id, name, subject, city)
books(id, teacher_id -> teachers.id, title, grade, term, pages, price)
orders(id, book_id -> books.id, quantity, order_date, status in {pending, delivered, cancelled})
""".strip()
