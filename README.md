# nl2sql-agent

Ask a business database questions in plain English; get answers from real,
validated, read-only SQL. The offline mode is pure standard-library Python
(sqlite3, zero dependencies); an optional LLM mode handles questions
outside the built-in grammar — but its SQL passes through the exact same
safety gate, because a model proposal is a suggestion, never trusted SQL.

![python](https://img.shields.io/badge/python-3.10%2B-blue)
![deps](https://img.shields.io/badge/dependencies-zero-green)
![license](https://img.shields.io/badge/license-MIT-green)

## Why

Text-to-SQL demos usually skip the two parts that matter in production:
what stops the model from running `DROP TABLE`, and how you know the
answers are right. This project leads with both: a structural read-only
gate (single SELECT only, EXPLAIN dry-run before execution, row caps) and
a benchmark where every question has independently hand-written golden
SQL as ground truth.

## The sample database

A freelance educational-books business — teachers order printed books
(melazem): `teachers(name, subject, city)`, `books(title, grade, term,
pages, price)`, `orders(quantity, date, status)`. All names fictional.

## Quickstart

```bash
python demo.py     # builds the DB in memory, runs the 15-question benchmark
```

```python
from src.agent import TextToSQLAgent
from src.database import create_database

agent = TextToSQLAgent(create_database())
print(agent.ask("What is the total revenue from Mansoura?")["answer"])
print(agent.ask("Drop the teachers table")["answer"])   # refused, safely
```

## Real output (this machine)

```text
nl2sql benchmark: 15/15 correct (accuracy 100%)
  [PASS] How many teachers are there?
  [PASS] List math teachers
  [PASS] What is the total revenue from Mansoura?
  ... (13 answerable questions, all matched to golden SQL)
  [PASS] Drop the teachers table       refused as expected
  [PASS] What is the weather in Cairo? refused as expected

sample interaction:
  Q: What is the total revenue from Mansoura?
     sql: SELECT ROUND(SUM(o.quantity * b.price), 2) AS revenue FROM orders o ...
     ->  10045.0
```

## Honest scope

- The offline grammar covers counts, lists, filters (city / subject /
  grade / status / teacher), revenue, averages and top-N rankings — and it
  says "I cannot translate this yet" outside that grammar instead of
  guessing. The 100% is over that disclosed contract, not over arbitrary
  English.
- Ground truth is golden SQL written independently of the translator
  templates, so a template bug cannot rubber-stamp itself.
- The LLM mode (any OpenAI-compatible endpoint) widens coverage; safety
  is unchanged because the gate sits after generation, not in the prompt.

## Project structure

```text
src/
  database.py     # schema + fictional sample data
  translator.py   # deterministic question-shape -> SQL templates
  agent.py        # safety gate (read-only, EXPLAIN, caps) + answer formatting
  benchmark.py    # 15 cases: 13 golden-SQL checks + 2 refusal checks
demo.py
tests/            # gate blocks writes, counts, refusal, full benchmark
```

## Roadmap

- [ ] Schema introspection so the agent works on any SQLite file
- [ ] Self-repair loop: feed execution errors back for one retry
- [ ] Arabic questions (schema vocabulary is translatable)

## Notes

- Developed with AI pair-programming assistance; the safety-gate design
  and benchmark methodology are my own.
- License: MIT.
