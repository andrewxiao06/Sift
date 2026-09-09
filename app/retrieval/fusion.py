from app.retrieval.bm25 import bm25_search
from app.retrieval.dense import dense_search 

def reciprocal_rank_fusion(
        bm25_results: list[dict],
        dense_results: list[dict],
        k: int = 60, 

) -> list[dict]:

    # 1. build a score dict: paper_id -> combined RRF score, starting empty
      # 2. for each list, walk through it enumerated (so you know each paper's rank),
      #    and for each paper add 1 / (k + rank) to its running score
      #    - watch off-by-one: is the first result rank 0 or rank 1? RRF is usually defined
  #with rank starting at 1
      # 3. you'll also need a way to get back full paper info (title, abstract) by id,
      #    since the score dict only tracks scores — think about how to keep that alongside
      # 4. sort paper ids by combined score, descending
      # 5. return them as a list, probably paper dicts with their score attached

    score_dict = {}
    id_to_paper = {}

    for rank, paper in enumerate(bm25_results):
        paper_id = paper["id"]
        score_dict[paper_id] = score_dict.get(paper_id, 0) + 1 / (k + rank + 1)
        id_to_paper[paper_id] = paper

    for rank, paper in enumerate(dense_results):
        paper_id = paper["id"]
        score_dict[paper_id] = score_dict.get(paper_id, 0) + 1 / (k + rank + 1)
        id_to_paper[paper_id] = paper

    # sort paper ids by combined score, descending
    sorted_papers = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    # return them as a list, probably paper dicts with their score attached
    return [{"paper_id": paper_id, "score": score, **id_to_paper[paper_id]} for paper_id, score in sorted_papers]


def hybrid_search(query: str, top_k: int = 10, candidate_pool: int = 100) -> list[dict]:
  # convenience wrapper: run both searches, fuse them, return top_k
  bm25_results = bm25_search(query, top_k = candidate_pool)
  dense_results = dense_search(query, top_k = candidate_pool)
  fused_results = reciprocal_rank_fusion(bm25_results, dense_results)
  return fused_results[:top_k]