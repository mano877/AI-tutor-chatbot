"""PostgreSQL database connection and operations using psycopg2."""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

# Database configuration from environment variables
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME", "tutor_chatbot")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")
DB_MIN_CONN = int(os.getenv("DB_MIN_CONN", "2"))
DB_MAX_CONN = int(os.getenv("DB_MAX_CONN", "10"))

_pool: ThreadedConnectionPool | None = None


def get_connection_pool() -> ThreadedConnectionPool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        dsn = (
            f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
            f"user={DB_USER} password={DB_PASSWORD}"
        )
        _pool = ThreadedConnectionPool(
            minconn=DB_MIN_CONN,
            maxconn=DB_MAX_CONN,
            dsn=dsn,
        )
    return _pool


@contextmanager
def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    """Get a database connection from the pool as a context manager."""
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db() -> None:
    """Initialize the database schema."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_student_id
                ON chat_messages(student_id);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp
                ON chat_messages(student_id, timestamp);
            """)


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


# ── Student CRUD ──────────────────────────────────────────────────────────

def create_student(name: str, email: str) -> dict:
    """Insert a new student and return their record."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO students (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at;",
                (name, email),
            )
            return dict(cur.fetchone())


def list_students() -> list[dict]:
    """Return all students ordered by creation time."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, created_at FROM students ORDER BY created_at DESC;"
            )
            return [dict(r) for r in cur.fetchall()]


def get_student(student_id: int) -> dict | None:
    """Get a single student by id, or None if not found."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, created_at FROM students WHERE id = %s;",
                (student_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def delete_student(student_id: int) -> bool:
    """Delete a student and all their chat messages. Returns True if deleted."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM students WHERE id = %s RETURNING id;",
                (student_id,),
            )
            return cur.fetchone() is not None


# ── Chat Message CRUD ──────────────────────────────────────────────────────

def add_chat_message(student_id: int, role: str, content: str) -> dict:
    """Insert a chat message and return it."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO chat_messages (student_id, role, content) VALUES (%s, %s, %s) RETURNING id, student_id, role, content, timestamp;",
                (student_id, role, content),
            )
            return dict(cur.fetchone())


def get_chat_history(student_id: int) -> list[dict]:
    """Return all messages for a student, oldest first."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, role, content, timestamp FROM chat_messages WHERE student_id = %s ORDER BY timestamp ASC;",
                (student_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def clear_chat_history(student_id: int) -> bool:
    """Delete all messages for a student."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chat_messages WHERE student_id = %s;",
                (student_id,),
            )
            return cur.rowcount > 0