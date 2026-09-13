"""Runs every retrieval variant against the graded query set and produces
the ablation table (docs/SPEC.md Week 2, Variant A-E).

Usage: uv run python -m eval.run_eval
"""

import json
import time
from collections import defaultdict
from pathlib import Path

from app.retrieval.bm25 import bm25_search
from app.retrieval.dense import dense_search
from app.retrieval.fusion import hybrid_search
from app.retrieval.rerank import reranked_search
from eval.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank

QRELS_PATH = Path(__file__).parent / "qrels.jsonl"
RESULTS_DIR = Path(__file__).parent.parent / "results"

TOP_K = 20  # matches the depth most queries were pooled/graded at

VARIANTS = {
    "dense": lambda q: dense_search(q, top_k=TOP_K),
    "bm25": lambda q: bm25_search(q, top_k=TOP_K),
    "hybrid": lambda q: hybrid_search(q, top_k=TOP_K),
    "reranked": lambda q: reranked_search(q, top_k=TOP_K),
}


def load_qrels() -> dict[str, dict[int, int]]:
    """query -> {paper_id: grade}, only for queries with at least one graded pair."""
    qrels_by_query: dict[str, dict[int, int]] = defaultdict(dict)
    with open(QRELS_PATH) as f:
        for line in f:
            record = json.loads(line)
            qrels_by_query[record["query"]][record["paper_id"]] = record["grade"]
    return dict(qrels_by_query)


def evaluate_variant(search_fn, queries: list[str], qrels_by_query: dict[str, dict[int, int]]) -> dict:
    """Runs one variant over all queries, returns per-metric averages and mean latency."""
    metrics = {"precision@10": [], "recall@20": [], "mrr": [], "ndcg@10": []}
    latencies = []

    for query in queries:
        qrels = qrels_by_query[query]

        start = time.perf_counter()
        results = search_fn(query)
        latencies.append(time.perf_counter() - start)

        retrieved_ids = [r["id"] for r in results]

        metrics["precision@10"].append(precision_at_k(retrieved_ids, qrels, 10))
        metrics["recall@20"].append(recall_at_k(retrieved_ids, qrels, TOP_K))
        metrics["mrr"].append(reciprocal_rank(retrieved_ids, qrels))
        metrics["ndcg@10"].append(ndcg_at_k(retrieved_ids, qrels, 10))

    averaged = {name: sum(vals) / len(vals) for name, vals in metrics.items()}
    averaged["mean_latency_ms"] = sum(latencies) / len(latencies) * 1000
    averaged["n_queries"] = len(queries)
    return averaged


def main():
    qrels_by_query = load_qrels()
    queries = sorted(qrels_by_query.keys())
    print(f"Evaluating against {len(queries)} graded queries\n")

    table = {}
    for variant_name, search_fn in VARIANTS.items():
        print(f"Running variant: {variant_name}...")
        table[variant_name] = evaluate_variant(search_fn, queries, qrels_by_query)

    # print ablation table
    header = f"{'variant':<10} {'precision@10':>13} {'recall@20':>10} {'mrr':>6} {'ndcg@10':>8} {'latency(ms)':>12}"
    print("\n" + header)
    print("-" * len(header))
    for variant_name, m in table.items():
        print(
            f"{variant_name:<10} {m['precision@10']:>13.3f} {m['recall@20']:>10.3f} "
            f"{m['mrr']:>6.3f} {m['ndcg@10']:>8.3f} {m['mean_latency_ms']:>12.1f}"
        )

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "ablation.json"
    with open(out_path, "w") as f:
        json.dump(table, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
