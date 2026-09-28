"""Measures per-query latency (p50/p95/mean) for each retrieval variant, plus a
per-stage split of the reranked pipeline (hybrid candidate gen vs cross-encoder).

Discards a warmup pass (MPS kernel compile / model load), then times REPEATS
passes over every graded query and pools the samples so p95 isn't one outlier.

Usage: uv run python -m eval.bench_latency [label]
  label defaults to "baseline"; writes results/latency_<label>.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

from app.retrieval.fusion import hybrid_search
from app.retrieval.rerank import rerank
from eval.run_eval import TOP_K, VARIANTS, load_qrels

RESULTS_DIR = Path(__file__).parent.parent / "results"
REPEATS = 5
CANDIDATE_POOL = 100


def summarize(samples_s: list[float]) -> dict:
    ms = np.array(samples_s) * 1000
    return {
        "p50_ms": float(np.percentile(ms, 50)),
        "p95_ms": float(np.percentile(ms, 95)),
        "mean_ms": float(ms.mean()),
        "n_samples": len(ms),
    }


def time_calls(fn, queries: list[str]) -> list[float]:
    samples = []
    for _ in range(REPEATS):
        for q in queries:
            start = time.perf_counter()
            fn(q)
            samples.append(time.perf_counter() - start)
    return samples


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    queries = sorted(load_qrels().keys())
    print(f"[{label}] {len(queries)} queries x {REPEATS} repeats\n")

    # warmup: one untimed pass through every variant
    for search_fn in VARIANTS.values():
        for q in queries:
            search_fn(q)

    out = {"label": label, "n_queries": len(queries), "repeats": REPEATS, "variants": {}, "reranked_stages": {}}

    for name, search_fn in VARIANTS.items():
        out["variants"][name] = summarize(time_calls(search_fn, queries))

    # per-stage split of reranked: hybrid candidate generation vs cross-encoder
    hybrid_samples, rerank_samples = [], []
    for _ in range(REPEATS):
        for q in queries:
            t0 = time.perf_counter()
            candidates = hybrid_search(q, top_k=CANDIDATE_POOL)
            t1 = time.perf_counter()
            rerank(q, candidates, TOP_K)
            t2 = time.perf_counter()
            hybrid_samples.append(t1 - t0)
            rerank_samples.append(t2 - t1)
    out["reranked_stages"] = {
        "hybrid_candidates": summarize(hybrid_samples),
        "cross_encoder": summarize(rerank_samples),
    }

    header = f"{'variant':<20} {'p50(ms)':>9} {'p95(ms)':>9} {'mean(ms)':>9}"
    print(header)
    print("-" * len(header))
    rows = {**out["variants"], **{f"  stage:{k}": v for k, v in out["reranked_stages"].items()}}
    for name, s in rows.items():
        print(f"{name:<20} {s['p50_ms']:>9.1f} {s['p95_ms']:>9.1f} {s['mean_ms']:>9.1f}")

    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"latency_{label}.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
