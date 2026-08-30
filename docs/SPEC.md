Sift — Project Spec v2
arXiv hybrid retrieval + agent Owner: Andrew Xiao Timebox: 4 weeks core (terminal-first) + 2 weeks web app Supersedes: arxiv-agent-spec.md

1. What this is
   A research assistant over arXiv that does two things well:

Retrieval that probably beats a baseline. Hybrid lexical + dense retrieval with cross-encoder reranking, measured against arXiv's native search on a hand-labeled query set.
An agent that uses that retrieval as a tool. Decomposes a research question into multiple searches, decides when it has enough evidence, and stops.

The headline deliverable is not the app. It is a number: retrieval quality before vs. after each pipeline stage, on a labeled set, with cost and latency attached.

Name: Sift. Short, describes the function, works as a CLI verb. Avoid PaperTrail (SolarWinds owns it in log management) and AI Research Assistant (reads as tutorial).
Non-goals — scope freeze
Cross-paper "research landscape" synthesis. Unfalsifiable, unevaluable, cut.
Multi-agent router/worker architectures. One agent, three tools.
Fine-tuning the embedding or reranker. Not enough labeled data; would likely make results worse.
Local LLM hosting, quantization, GPU serving.
LangChain, LlamaIndex, or any orchestration framework.
Auth and user accounts.

If a feature isn't required to produce or defend the headline number, it's out.

2. Hardware
   MacBook M3, PyTorch MPS backend. PYTORCH_ENABLE_MPS_FALLBACK=1.

The RTX 3050 is not used. 4GB VRAM buys nothing for small encoders; realistic time saved across the project is minutes (Week 1 is hand-grading, Weeks 3–4 are API-bound); and splitting machines breaks measurement consistency. All latency numbers must come from one device or they aren't defensible.

3. Technology stack
   Language / ML runtime Python 3.11 · PyTorch (MPS) · Hugging Face transformers (used directly for the hand-written mean-pooling embedding path) · sentence-transformers with BAAI/bge-small-en-v1.5 · cross-encoder ms-marco-MiniLM-L-6-v2 · rank_bm25 · NumPy

Backend FastAPI + Uvicorn · Pydantic v2 · SQLAlchemy · Anthropic/OpenAI SDK directly for tool calling, no framework

Data PostgreSQL + pgvector (HNSW) · arxiv client · Redis for query-embedding cache (optional; a dict works in v1)

Frontend — Phase 2 Next.js + TypeScript + Tailwind · Server-Sent Events for agent trace streaming

Infra / tooling Docker · Vercel (frontend) + Railway or Fly.io (API + Postgres) · pytest · GitHub Actions running make eval · Git

Genuinely new to you: PyTorch, Hugging Face, sentence-transformers, cross-encoders, BM25, evaluation metrics. Everything else is already shipped experience — which is why the spec keeps that half thin.

4. Corpus
   2–3 categories only (cs.IR, cs.CL, optionally cs.LG)
   ~2,000 papers, last 24 months
   Stored: arxiv_id, title, abstract, authors, categories, dates, PDF URL
   Abstract-only embedding in v1; section chunking is a Week 2 experiment

Chunking decision — record it, don't hand-wave it. v1 embeds title + abstract as one unit. If section chunking gets tested, document chunk size, overlap, and whether nDCG improved. A negative result is a legitimate finding.

5. Week 1 — Baseline and eval set
   The foundation. Do it before anything enjoyable. This is the part almost every student project skips, and skipping it is why those projects are interchangeable.
   5.1 Query selection — 40 queries, hand-written
   Type
   Example
   Purpose
   Concept
   "reducing hallucination in retrieval systems"
   tests dense retrieval
   Named entity
   "ColBERT late interaction"
   tests lexical — dense fails these
   Descriptive
   "making language models cite their sources"
   tests semantic gap
   Comparative
   "sparse vs dense retrieval tradeoffs"
   tests multi-aspect matching

~10 each. The named-entity group exists to expose where pure semantic search breaks. That failure is the motivation for hybrid retrieval in Week 2, and explaining it is the point.
5.2 Grading rubric — graded relevance 0–3
Grade the pooled top-20 from every retrieval variant, not just the baseline. Otherwise a later variant surfaces a great paper you never judged, it counts as irrelevant, and the ablation table lies in the wrong direction.

Grade
Meaning
3
Directly answers the query; a core paper
2
Substantially relevant, not the primary contribution
1
Tangential; same subfield, different question
0
Not relevant

Consistency protocol: grade all 40 in one sitting. Re-grade a random 10% two days later and compute self-agreement. Below ~80% means the rubric is mush — tighten and re-grade. Report the number in the README; it bounds how much any measured improvement can be trusted.

Store in data/qrels.jsonl, versioned in git. Most valuable artifact in the repo.
5.3 Metrics
nDCG@10 (primary) · precision@10 · MRR · recall@100 (the ceiling reranking can reach — if stage-1 recall is bad, no reranker saves you).

Implement nDCG by hand. ~20 lines, and you need to explain DCG, the ideal-DCG normalizer, and why graded beats binary.
5.4 Two baselines
arXiv native search — honest external baseline
Naive dense top-k — the "what every student builds" baseline

Exit condition: both baselines recorded in results/.

6. Week 2 — Retrieval work
   Add one stage at a time, re-measure after each. The ablation table is the single best interview artifact this project produces.

Variant
Record
A
Dense only
nDCG@10, p@10, latency
B
BM25 only
same
C
Hybrid via reciprocal rank fusion
same + RRF k
D
Hybrid → cross-encoder rerank top 100
same + rerank latency
E
Rerank top 50
recall/latency tradeoff

Expect and explain: BM25 wins named-entity queries, dense wins descriptive, hybrid beats both; cross-encoder gives the biggest nDCG jump and the most latency; 50 vs 100 is a deliberate tradeoff.

Also record: cross-encoder wall-clock on MPS, encode throughput, index build time.

7. Week 3 — The agent
   Single agent, native SDK tool calling, three tools.

Tool
Signature
Notes
search_papers
(query, k) → ranked papers
full Week 2 pipeline
get_paper
(arxiv_id) → structured record
Pydantic-validated
compare_papers
(ids, dimension) → comparison
max 5 ids

Loop control

Max 6 iterations, enforced in code, never only in the prompt
Token budget per request; abort and return partial results
Malformed args → return validation error to the model, 2 retries, then fail gracefully
Empty results → explicit "no results" record, never an exception. The agent must reason about a failed search.
Trace every step: iteration, tool, args, latency, tokens

Prompt versioning. Prompts live in prompts/ with a version string. Any change requires re-running the eval set. This is the "regression testing a nondeterministic system" story — rare on a student resume.

8. Week 4 — Prove it and stop
   Agent eval — 30 questions, separate from the retrieval queries, each with known-good papers.

Task success rate
Citation precision
Mean iterations to answer
Failure taxonomy: iteration cap / tool errors / wrong decomposition / stopped too early

The taxonomy is what most people skip and what sounds most senior in an interview.

Cost and latency: tokens per query, cost per query, p95 end-to-end and per stage, cache hit rate and its delta.
Phase 1 definition of done
qrels.jsonl committed, 40 queries graded, self-agreement reported
Ablation table A–E
Agent eval: 30 questions, success rate, failure taxonomy
Cost/query and p95 documented
README with architecture diagram and results tables
make eval reproduces every number from a clean checkout
Terminal demo under 60 seconds

No frontend commits until this list is checked.

9. Phase 2 (Weeks 5–6) — The web app
   Not a rescope. An added phase, after Phase 1 is done.

The point: make the evaluation visible. A plain search box is forgettable — every student project has one. A search box with a mode toggle (dense / BM25 / hybrid / reranked) where results reorder live and latency plus nDCG display beside them is a demo of your engineering, not a demo of arXiv.

One page, no auth
Search with mode toggle and per-mode timing
Results with relevance scores exposed
Agent view streaming the trace over SSE — watch it decide, call tools, stop
Static results page rendering the ablation table and failure taxonomy
Deploy: Vercel + Railway/Fly. Skip AWS — a weekend of IAM for zero learning.

Constraints. Deployed cross-encoder runs CPU inference on a small instance; expect worse p95 than the M3 and report both. "640ms local, 1.4s deployed on shared CPU" is a stronger interview answer than a fast number you can't reproduce live. Rate-limit the agent endpoint before it's public or a scraper spends your API budget overnight.

10. Route skeleton
    POST /api/search

           body: { query, k?, mode? }     mode ∈ {dense, bm25, hybrid, reranked}

           resp: { results[], timings{}, mode }

           note: mode exists so the ablation runs through the API,

                 not just the eval script

GET /api/papers/{arxiv_id} resp: { paper, extraction }

POST /api/compare

       body: { arxiv_ids[], dimension }

       resp: { comparisons[], dimension }

POST /api/agent/query

       body: { question, max_iterations? }

       resp: { answer, citations[], trace[], usage{} }

POST /api/agent/query/stream SSE — one event per iteration

POST /admin/ingest body: { categories[], max_results, since? }

POST /admin/reindex

GET /health
Repo layout
sift/

├── app/

│ ├── api/ # route handlers

│ ├── ingest/ # arxiv client, normalization

│ ├── retrieval/ # bm25, dense, fusion, rerank

│ ├── extraction/ # pydantic schemas

│ ├── agent/ # loop, tool registry, trace

│ └── models/ # db models, encoders

├── prompts/ # versioned prompt files

├── eval/

│ ├── qrels.jsonl

│ ├── agent_tasks.jsonl

│ ├── metrics.py # hand-written

│ └── run_eval.py

├── results/ # ablation tables, committed

├── web/ # Phase 2 only

├── tests/

└── README.md

11. Resume bullets
    Numbers below are placeholders showing shape. Replace with what make eval prints. If a number can't be regenerated on demand, delete the bullet.

Sift | Python, PyTorch, FastAPI, PostgreSQL, pgvector, Next.js, Docker Sep 2026 – Present

Built a hybrid retrieval pipeline over 2,000 arXiv papers combining BM25 and dense embeddings via reciprocal rank fusion with cross-encoder reranking, raising nDCG@10 from 0.41 to 0.68 against the arXiv search baseline on a 40-query hand-labeled set.
Implemented graded-relevance evaluation (nDCG, precision@k, MRR) from scratch and gated prompt and model changes on eval regression, catching 3 changes that degraded retrieval quality.
Engineered an LLM agent with native tool calling, bounded iteration, and schema-validated tool arguments, reaching 73% task success across 30 research questions across 4 classified failure modes.
Cut p95 query latency from 1.9s to 640ms via query embedding caching and rerank depth tuning, serving a Next.js interface at $0.011 per query.

Why these work: a named baseline with before-and-after, a stated denominator, and a cost figure. Almost no student resume has any of the three. That's the edge — not the topic.

Skills additions (only once actually in the repo): PyTorch, Hugging Face Transformers, sentence-transformers, NumPy under Frameworks; Vercel, Railway under Infrastructure.

12. Sequencing
    Close out PyLog first — benchmark, README, architecture diagram, 60-second demo. Two weekends; the hard parts are already built and what remains is proof.
    Sift Phase 1 — 4 weeks, terminal-first.
    Sift Phase 2 — 2 weeks, web app, only if Phase 1 is done.

Both PyLog and Sift belong on the resume. PyLog carries systems depth, Sift carries AI engineering; neither replaces the other. Dropping PyLog leaves four AI/full-stack projects and nothing demonstrating infrastructure ability — and it's currently the strongest interview generator on the page.

Sift replaces Menu Translator. Final project section: Sift, PyLog, ShuttleRank, RU My Valentine — one AI, one systems, two full-stack.

Referral outreach runs in parallel the entire time. It's at zero and remains the highest-leverage activity of the fall. No project ships fast enough to matter for this application cycle; referrals do.
