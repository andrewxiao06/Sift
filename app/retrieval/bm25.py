from rank_bm25 import BM25Okapi

from app.models.db import get_connection


#best matching 25 documents for relevance based on the query (user prompt)

def load_corpus() -> tuple[list[dict], BM25Okapi]:
    # 1. fetch all papers (id, title, abstract) from the DB — same cursor pattern as before
      # 2. tokenize each abstract into a list of words (simplest: text.lower().split())
      # 3. build BM25Okapi(tokenized_corpus)
      # 4. return (papers, bm25_index) — papers is your list in the SAME order used to build the index,
      #    so index i in bm25's scores always corresponds to papers[i]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, abstract FROM papers")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    papers = []
    tokenized = []
    for r in rows:
        paper = {"id": r[0], "title": r[1], "abstract": r[2]}
        tokens = paper["abstract"].lower().split()
        papers.append(paper)
        tokenized.append(tokens)

    bm25 = BM25Okapi(tokenized)

    return papers, bm25

_papers, _bm25 = load_corpus()

def bm25_search(query: str, top_k: int = 10) -> list[dict]:
      tokenized_query = query.lower().split()
      return _bm25.get_top_n(tokenized_query, _papers, n=top_k)

