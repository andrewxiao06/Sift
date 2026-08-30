"""Fetches paper metadata from the arXiv API and upserts it into Postgres."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import arxiv

from app.config import ARXIV_CATEGORIES, ARXIV_MAX_RESULTS, ARXIV_MONTHS_BACK
from app.ingest.normalize import normalize
from app.models.db import get_connection

_client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)

UPSERT_SQL = """
INSERT INTO papers (arxiv_id, title, abstract, authors, categories, published, updated, pdf_url)
VALUES (%(arxiv_id)s, %(title)s, %(abstract)s, %(authors)s, %(categories)s,
        %(published)s, %(updated)s, %(pdf_url)s)
ON CONFLICT (arxiv_id) DO UPDATE SET
    title = EXCLUDED.title,
    abstract = EXCLUDED.abstract,
    authors = EXCLUDED.authors,
    categories = EXCLUDED.categories,
    updated = EXCLUDED.updated,
    pdf_url = EXCLUDED.pdf_url;
"""


def fetch_papers(
    categories: list[str] = ARXIV_CATEGORIES,
    max_results: int = ARXIV_MAX_RESULTS,
    months_back: int = ARXIV_MONTHS_BACK,
) -> Iterator[arxiv.Result]:
    """Yields arXiv results in the given categories, newest first, stopping once
    results fall outside the months_back window (results are sorted by date so
    this avoids paging through the entire category history).
    """
    query = " OR ".join(f"cat:{c}" for c in categories)
    cutoff = datetime.now(UTC) - timedelta(days=30 * months_back)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    for result in _client.results(search):
        if result.published < cutoff:
            break
        yield result


def ingest(
    categories: list[str] = ARXIV_CATEGORIES,
    max_results: int = ARXIV_MAX_RESULTS,
    months_back: int = ARXIV_MONTHS_BACK,
) -> int:
    """Fetches, normalizes, and upserts papers by arxiv_id. Returns count written."""
    conn = get_connection()
    count = 0
    try:
        with conn.cursor() as cur:
            for result in fetch_papers(categories, max_results, months_back):
                record = normalize(result)
                cur.execute(UPSERT_SQL, record)
                count += 1
                if count % 100 == 0:
                    conn.commit()
        conn.commit()
    finally:
        conn.close()
    return count
