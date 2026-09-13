"""Interactive grading tool: pools top-20 results from every retrieval variant
for each query, prompts for a 0-3 relevance grade per paper, and appends
graded (query, paper_id, grade) records to eval/qrels.jsonl.

Safe to stop and resume — already-graded (query, paper_id) pairs are skipped.

Run with: uv run python eval/grade.py
"""

import json
from pathlib import Path

from app.retrieval.bm25 import bm25_search
from app.retrieval.dense import dense_search
from app.retrieval.fusion import hybrid_search
from app.retrieval.rerank import reranked_search
from eval.queries import ALL_QUERIES

QRELS_PATH = Path(__file__).parent / "qrels.jsonl"

GRADE_MEANINGS = {
    "0": "not relevant",
    "1": "tangential; same subfield, different question",
    "2": "substantially relevant, not the primary contribution",
    "3": "directly answers the query; a core paper",
}


def load_already_graded() -> set[tuple[str, int]]:
    if not QRELS_PATH.exists() or QRELS_PATH.stat().st_size == 0:
        return set()
    graded = set()
    with open(QRELS_PATH) as f:
        for line in f:
            record = json.loads(line)
            graded.add((record["query"], record["paper_id"]))
    return graded


def pool_candidates(query: str, top_k: int = 20) -> list[dict]:
    variants = [
        dense_search(query, top_k=top_k),
        bm25_search(query, top_k=top_k),
        hybrid_search(query, top_k=top_k),
        reranked_search(query, top_k=top_k),
    ]

    seen_ids = set()
    pooled = []
    for results in variants:
        for paper in results:
            if paper["id"] not in seen_ids:
                seen_ids.add(paper["id"])
                pooled.append(paper)
    return pooled


def prompt_grade(query: str, paper: dict) -> int | None:
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print(f"PAPER: {paper['title']}")
    print(f"ABSTRACT: {paper['abstract'][:400]}...")
    print("-" * 80)
    print("Grade: 0=not relevant  1=tangential  2=substantial  3=core paper  (s=skip, q=quit)")

    while True:
        choice = input("Grade > ").strip().lower()
        if choice == "q":
            return None
        if choice == "s":
            return -1
        if choice in GRADE_MEANINGS:
            return int(choice)
        print("Invalid input, try again.")


def main():
    already_graded = load_already_graded()
    print(f"{len(already_graded)} (query, paper) pairs already graded, resuming.")

    with open(QRELS_PATH, "a") as out:
        for query in ALL_QUERIES:
            candidates = pool_candidates(query)
            for paper in candidates:
                if (query, paper["id"]) in already_graded:
                    continue

                grade = prompt_grade(query, paper)
                if grade is None:
                    print("Quitting. Progress saved.")
                    return
                if grade == -1:
                    continue

                record = {"query": query, "paper_id": paper["id"], "grade": grade}
                out.write(json.dumps(record) + "\n")
                out.flush()
                already_graded.add((query, paper["id"]))

    print("All queries graded.")


if __name__ == "__main__":
    main()
