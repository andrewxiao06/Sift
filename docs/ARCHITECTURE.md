# Sift — Architecture Decisions

A running log of *why* the system is built the way it is, not just what it does. Each section should be enough to defend the decision unaided in an interview. Written incrementally as the project progresses — see `docs/SPEC.md` for the full plan and `results/` for the numbers that back these decisions up once `make eval` exists.

Status as of this writing: corpus ingestion, embedding pipeline, dense retrieval, and BM25 retrieval are built and manually verified. Fusion, reranking, and evaluation are not yet implemented — sections below are written up to the current state and will be extended as those land.

---

## 1. Why hybrid retrieval at all (BM25 + dense), instead of just one

Two different retrieval methods fail in different, complementary ways, and neither one alone is safe to ship:

- **Dense (embedding) retrieval** matches by *meaning*. It's strong when a query is phrased differently from the paper's own language — a query like "making language models cite their sources" should surface papers about attribution/grounding even if none of them use that exact phrase. Its weakness: it can drift toward semantically-adjacent-but-wrong results, and it's genuinely bad at exact terminology — a query for a specific named method (e.g. "ColBERT late interaction") isn't a *concept* to embed, it's a lookup, and dense retrieval has no special mechanism for "this exact term must appear."

- **BM25 (lexical/keyword) retrieval** matches by *exact term overlap*, weighted by how rare and how repeated each term is (see §4). It's strong exactly where dense is weak: named entities, acronyms, specific method names. Its weakness is the inverse — it has no notion of meaning, so a query and a relevant paper that use different words for the same idea will score poorly even though a human would call them a perfect match.

Shipping only one method means picking one failure mode over the other. The named-entity query group in the eval set (`docs/SPEC.md` §5.1) exists specifically to make this failure visible and measurable, not just asserted — the plan is to show BM25 winning on named-entity queries and dense winning on descriptive/conceptual queries, then show hybrid beating both, with numbers in `results/`, not just a claim.

## 2. Why BM25 specifically (not just "keyword search")

BM25 improves on naive keyword counting in three ways that matter for a corpus of abstracts:

- **Diminishing returns on term frequency.** A paper mentioning "retrieval" 10 times isn't 10x more about retrieval than one mentioning it once — BM25's scoring saturates so repeated mentions add less and less, instead of letting a paper win purely by repeating a word.
- **Inverse document frequency (IDF).** Common words ("the", "model", "using") carry almost no signal since they appear everywhere; rare, distinctive words (a specific method name) get weighted heavily because their presence is much more informative.
- **Length normalization.** A longer abstract naturally has more chances to contain a query term by coincidence. BM25 corrects for document length so short, precisely on-topic abstracts aren't penalized against long ones.

Implementation-wise, `rank_bm25`'s `BM25Okapi` builds an in-memory index over the whole corpus at load time (`load_corpus()` in `app/retrieval/bm25.py`), tokenizing each abstract with a simple `.lower().split()`. This is intentionally the simplest possible tokenizer — no stemming, no stopword removal — because the corpus is small (~2,000 abstracts) and the goal for v1 is a working, explainable baseline, not a maximally tuned lexical index. If BM25 underperforms on certain query types during eval, tokenizer quality is a documented, revisitable knob, not a silent assumption.

## 3. Why dense retrieval uses `BAAI/bge-small-en-v1.5`, and why the embedding path is hand-written

**Model choice**: `bge-small-en-v1.5` is a small (384-dim), fast bi-encoder that runs comfortably on an M3's MPS backend without needing GPU serving infrastructure — consistent with the project's explicit non-goal of local LLM hosting/GPU serving (`docs/SPEC.md` non-goals). It's a well-established general-purpose English embedding model, appropriate for a ~2,000-paper corpus where fine-tuning isn't justified (also an explicit non-goal — not enough labeled data, and fine-tuning risks making results worse without enough data to validate against).

**Why the embedding path (tokenize → forward → mean pool → normalize) is hand-written in `app/models/encoders.py` instead of using `sentence-transformers`' one-line `.encode()`**: this is a deliberate learning decision, not a technical requirement — `sentence-transformers` is even listed in the stack (`docs/SPEC.md` §3) and could do this in one call. Writing it by hand via raw `transformers` forces understanding of every step:

- **Tokenization** turns text into integer IDs the model can process, plus an attention mask marking real tokens vs. padding.
- **Forward pass** produces one vector per *token*, not per document — `last_hidden_state` has shape `(batch, seq_len, hidden_dim)`.
- **Mean pooling** collapses per-token vectors into one per-document vector by averaging, using the attention mask so padding tokens (which carry no real information) don't dilute the average.
- **L2 normalization** scales every embedding to unit length, which is what makes cosine similarity (and pgvector's `<=>` cosine-distance operator) meaningful — without it, a vector's raw magnitude could distort similarity comparisons independent of its direction (i.e. its actual meaning).

This matters for the interview-readiness goal explicitly stated in `CLAUDE.md`: "why two-stage retrieval, what does a cross-encoder do that a bi-encoder can't" requires actually understanding what a bi-encoder produces and why, not just calling a library function that hides it.

## 4. Why Postgres + pgvector, and why raw SQL via psycopg instead of an ORM

**Postgres + pgvector** over alternatives like a dedicated vector DB (Pinecone, Weaviate, etc.) or MySQL: pgvector adds vector similarity search (cosine distance via `<=>`, HNSW indexing) directly inside a normal relational database. This means paper metadata (title, authors, categories, dates) and its embedding live in the *same row of the same table*, queryable with plain SQL — no separate system to keep in sync, no extra infrastructure to run and pay for, and it fits Postgres's designed role in the stack. For a ~2,000-row corpus, the operational simplicity of one database outweighs anything a dedicated vector database would offer at scale.

**Raw SQL via `psycopg` (v3) instead of SQLAlchemy**: originally the project used SQLAlchemy, then deliberately migrated off it. The reasoning: for a project this size, an ORM adds a layer of abstraction (model classes, session management, query-building DSL) whose main benefit — insulating the app from SQL — isn't needed when there's one table and a handful of queries. Writing raw SQL directly also means every query's actual cost and behavior is visible and explainable, which matters for a project whose stated purpose is depth of understanding over convenience. `pgvector.psycopg.register_vector(conn)` is registered once per connection (`app/models/db.py`) so that Python lists of floats can be written to/read from `vector` columns directly, without a hand-rolled serialization layer.

One sharp edge worth understanding for its own sake: Postgres infers a parameter's type from context. In an `UPDATE ... SET embedding = %s` statement, Postgres knows the target column's type (`vector(384)`) and can cast the incoming Python list correctly. But in a bare `WHERE embedding <=> %s` clause with no column being assigned to, there's no such context — Postgres defaults to guessing `double precision[]`, and `<=>` isn't defined between `vector` and `double precision[]`. The fix is an explicit cast in the SQL itself (`%s::vector`). This isn't a workaround for a bug — it's a real consequence of how type inference works for query parameters, and a concrete example of what raw SQL surfaces that an ORM would likely have hidden entirely.

## 5. Why the corpus is abstract-only, ~2,000 papers, and recency-biased (v1 tradeoff)

**Abstract-only embedding** (not full paper text or section chunking): explicitly a v1 scope decision per `docs/SPEC.md` — chunking is a later experiment, not a prerequisite. Embedding the abstract keeps each paper as one unit, one embedding, avoiding the added complexity of chunk size/overlap/aggregation before the baseline pipeline even works end to end. If section chunking is added later, `docs/SPEC.md` explicitly requires documenting chunk size, overlap, and whether it actually improved nDCG — including a negative result, if that's what happens.

**Recency-biased corpus (2,000 papers spanning ~24 days, not the originally intended 24 months)**: this is a known, deliberately-accepted tradeoff, not an oversight. The `arxiv` API query in `fetch_papers()` (`app/ingest/arxiv_client.py`) sorts by submission date descending and takes the newest `max_results`. For high-volume categories like `cs.CL`, more than 2,000 papers are submitted within a single month, so the `max_results` cap is hit long before the intended `months_back` cutoff ever takes effect — the corpus ends up newest-first and narrow in time range rather than spread across two years. The alternative (sampling a fixed number of papers per month across the full window) was considered and explicitly not implemented for v1, in favor of shipping a working pipeline first. This is a real limitation worth stating plainly in any interview discussion of the corpus, not glossing over — recency bias means the corpus may under-represent older, foundational work that a query like "ColBERT late interaction" (from the eval query set) might expect to find.

## 6. Why `uv` for dependency management

`uv` manages both the Python environment and locks exact dependency versions in `uv.lock` (as opposed to `pyproject.toml`, which expresses loose intended version ranges). This directly serves the project's core invariant: `make eval` must reproduce every number in `results/` from a clean checkout. If the exact resolved version of `torch`, `transformers`, or any other dependency drifted between runs, embeddings or scores could shift in ways that would make a measured result non-reproducible — which, per the working agreement, means the number doesn't exist. `uv.lock` is committed to git for exactly this reason (unlike `.venv/`, which is regenerable and gitignored).

---

*Next sections to add as the project progresses: fusion (reciprocal rank fusion — why RRF over raw score combination), cross-encoder reranking (why a second, slower stage after retrieval), evaluation metric design (nDCG vs. precision@k vs. MRR, why graded relevance over binary), and the agent's tool-calling/iteration design once built.*
