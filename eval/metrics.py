import math

def precision_at_k(retrieved_ids: list[int], qrels: dict[int, int], k: int) -> float:
    # qrels: paper_id -> grade (0-3) for THIS query. Treat grade > 0 as "relevant".
    # 1. take the first k ids from retrieved_ids
    # 2. count how many have qrels.get(id, 0) > 0
    # 3. divide by k

    paper_id  = retrieved_ids[:k]
    relevant_count = sum(1 for paper_id in paper_id if qrels.get(paper_id, 0) > 0)
    return relevant_count / k if k > 0 else 0.0


def reciprocal_rank(retrieved_ids: list[int], qrels: dict[int, int]) -> float:
      # 1. walk retrieved_ids in order (rank = position + 1)
      # 2. find the FIRST id where qrels.get(id, 0) > 0
      # 3. return 1 / rank, or 0.0 if none found

      for id in retrieved_ids:
          if qrels.get(id, 0) > 0:
              return 1 / (retrieved_ids.index(id) + 1)
      return 0.0


def recall_at_k(retrieved_ids: list[int], qrels: dict[int, int], k: int) -> float:
    # 1. total_relevant = count of qrels values > 0 (across ALL of qrels, not just top k)
      # 2. found = count of relevant ids within retrieved_ids[:k]
      # 3. return found / total_relevant (careful: what if total_relevant is 0?)
    total_relevant = sum(1 for grade in qrels.values() if grade > 0)
    found = sum(1 for id in retrieved_ids[:k] if qrels.get(id, 0) > 0)
    return found / total_relevant if total_relevant > 0 else 0.0


def dcg_at_k(grades: list[int], k: int) -> float:
      # grades: relevance grades IN RANKED ORDER (already looked up via qrels)
      # sum of grade / log2(rank + 1) for rank 1..k (rank is 1-indexed!)
    
    grades = grades[:k]
    dcg = 0.0
    for rank, grade in enumerate(grades, start=1):
        dcg += grade / math.log2(rank + 1)
    return dcg



def ndcg_at_k(retrieved_ids: list[int], qrels: dict[int, int], k: int) -> float:
    # 1. build `grades`: for each id in retrieved_ids[:k], look up qrels.get(id, 0)
      # 2. actual_dcg = dcg_at_k(grades, k)
      # 3. ideal_grades = sorted(qrels.values(), reverse=True)[:k]  <- the best possibleordering
      # 4. ideal_dcg = dcg_at_k(ideal_grades, k)
      # 5. return actual_dcg / ideal_dcg, guarding against ideal_dcg == 0
    
    grades = [qrels.get(id, 0) for id in retrieved_ids[:k]]
    actual_dcg = dcg_at_k(grades, k)
    ideal_grades = sorted(qrels.values(), reverse=True)[:k]
    ideal_dcg = dcg_at_k(ideal_grades, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0