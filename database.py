import sqlite3
from datetime import date

DB_PATH = "problems.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the problems table if it does not already exist."""
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem TEXT,
                who_has_it TEXT,
                pain_score INTEGER,
                is_opportunity BOOLEAN,
                category TEXT,
                source TEXT,
                date_found DATE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_problems(problems_list, source):
    """Save each problem dict to the database, skipping duplicate problem text.

    Returns the number of new rows inserted.
    """
    conn = _connect()
    inserted = 0
    today = date.today().isoformat()
    try:
        for item in problems_list:
            problem_text = item.get("problem")
            if not problem_text:
                continue

            existing = conn.execute(
                "SELECT 1 FROM problems WHERE problem = ?", (problem_text,)
            ).fetchone()
            if existing:
                continue

            conn.execute(
                """
                INSERT INTO problems
                    (problem, who_has_it, pain_score, is_opportunity,
                     category, source, date_found)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    problem_text,
                    item.get("who_has_it"),
                    item.get("pain_score"),
                    item.get("is_opportunity"),
                    item.get("category"),
                    source,
                    today,
                ),
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    return inserted


def get_todays_problems():
    """Return all problems found today, ordered by pain_score descending."""
    today = date.today().isoformat()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM problems
            WHERE date_found = ?
            ORDER BY pain_score DESC
            """,
            (today,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_problems():
    """Return every problem in the database."""
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM problems").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# Initialise the database on import.
init_db()
