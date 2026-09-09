from sentence_transformers import CrossEncoder

from app.config import CROSS_ENCODER_MODEL_NAME, DEVICE
from app.retrieval.fusion import hybrid_search

cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL_NAME, device=DEVICE)

def rerank(query: str, candidates: list[dict], top_k: int = 10) -> list[dict]:
    # 1. build a list of (query, abstract) pairs, one per candidate
      #    — this is the "joint input" the cross-encoder scores
      # 2. call _cross_encoder.predict(pairs) — returns a list/array of scores, same order as candidates
      # 3. attach each score back onto its candidate (e.g. candidate["rerank_score"] = score)
      # 4. sort candidates by that score, descending
      # 5. return the top_k

    pairs = [[query, candidate["abstract"]] for candidate in candidates]
    scores = cross_encoder.predict(pairs)

    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = score

    sorted_candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return sorted_candidates[:top_k]

def reranked_search(query: str, top_k: int = 10, candidate_pool: int = 100) -> list[dict]:
      # convenience wrapper: hybrid_search for candidates, then rerank them
      candidates = hybrid_search(query, top_k=candidate_pool)
      return rerank(query, candidates, top_k)