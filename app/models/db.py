"""Raw SQL database access via psycopg. No ORM by choice."""

import psycopg
from pgvector.psycopg import register_vector

from app.config import DATABASE_URL, EMBEDDING_DIM

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    categories TEXT[] NOT NULL,
    published TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    pdf_url TEXT NOT NULL,
    embedding VECTOR({EMBEDDING_DIM})
);
"""


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
