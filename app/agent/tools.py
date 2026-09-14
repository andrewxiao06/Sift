"""Tool implementations the agent can call, plus their Anthropic tool-use
schemas. Tools never raise into the agent loop — errors and empty results
come back as explicit structured records.
"""

from pydantic import ValidationError

from app.extraction.schemas import Paper
from app.models.db import get_connection
from app.retrieval.rerank import reranked_search


def search_papers(query: str, k: int = 10) -> dict:
    results = reranked_search(query, top_k=k)
    if not results:
        return {"results": [], "message": "No results found for this query."}
    return {
        "results": [
            {"arxiv_id": r["arxiv_id"], "title": r["title"], "abstract": r["abstract"]}
            for r in results
        ]
    }


def get_paper(arxiv_id: str) -> dict:
    conn = get_connection()
    cur = conn.execute(
        "SELECT id, arxiv_id, title, abstract, authors, categories, pdf_url "
        "FROM papers WHERE arxiv_id = %s",
        (arxiv_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return {"error": f"No paper found with arxiv_id {arxiv_id}."}

    columns = ["id", "arxiv_id", "title", "abstract", "authors", "categories", "pdf_url"]
    record = dict(zip(columns, row))

    try:
        paper = Paper(**record)
    except ValidationError as e:
        return {"error": f"Paper record failed validation: {e}"}

    return paper.model_dump()


def compare_papers(arxiv_ids: list[str], dimension: str) -> dict:
    if len(arxiv_ids) > 5:
        raise ValueError("compare_papers accepts at most 5 arxiv_ids.")

    papers = []
    missing = []
    for arxiv_id in arxiv_ids:
        result = get_paper(arxiv_id)
        if "error" in result:
            missing.append(arxiv_id)
        else:
            papers.append(result)

    return {
        "dimension": dimension,
        "papers": papers,
        "missing": missing,
    }


TOOL_DEFINITIONS = [
    {
        "name": "search_papers",
        "description": "Searches the paper corpus and returns the top-k most relevant papers for a query, using hybrid retrieval with reranking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "k": {"type": "integer", "description": "Number of results to return.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_paper",
        "description": "Fetches the full structured record for a single paper by its arxiv_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "arxiv_id": {"type": "string", "description": "The arXiv identifier, e.g. '2608.03860'."},
            },
            "required": ["arxiv_id"],
        },
    },
    {
        "name": "compare_papers",
        "description": "Compares up to 5 papers along a given dimension (e.g. methodology, results).",
        "input_schema": {
            "type": "object",
            "properties": {
                "arxiv_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Up to 5 arXiv identifiers to compare.",
                },
                "dimension": {"type": "string", "description": "What aspect to compare, e.g. 'methodology'."},
            },
            "required": ["arxiv_ids", "dimension"],
        },
    },
]

TOOL_DISPATCH = {
    "search_papers": search_papers,
    "get_paper": get_paper,
    "compare_papers": compare_papers,
}
