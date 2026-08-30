CLAUDE.md
Working agreement for Claude Code in this repo. Project name: Sift. Full spec in docs/SPEC.md.

Project
Hybrid retrieval (BM25 + dense + cross-encoder rerank) over ~2K arXiv papers, plus an agent that uses retrieval as a tool. Phase 2 adds a Next.js interface.

The deliverable is a measured result, not an app. Every feature exists to produce or defend a number in results/. If a change doesn't move a metric or make one reproducible, it's out of scope.

Owner is a student learning this domain. Speed matters, but the learning is the point. The working agreement below is not optional.

Working agreement
I write these myself — Claude explains and reviews, does NOT author
These are the learning surface. Claude may explain concepts, sketch pseudocode on request, review my implementation, and find bugs — but must not write them:

eval/metrics.py — nDCG, precision@k, MRR, recall@k
app/retrieval/ — fusion logic, rerank flow, score normalization
app/agent/ — the agent loop, iteration control, stop conditions
The raw transformers embedding path (tokenize → forward → mean pool → normalize)

If I ask Claude to write one of these, push back and confirm I'm sure before complying. These are the four things an interviewer will ask me to explain line by line.
Claude writes freely — plumbing I already know
FastAPI routes, request/response models
SQLAlchemy models, migrations, pgvector setup
arXiv ingestion, retry/backoff, normalization
Dockerfile, Makefile, CI, test scaffolding
Next.js components, Tailwind, SSE client wiring (Phase 2)
README structure, tables, diagrams
Always
Explain the why behind a design choice in 2–3 sentences before the code.
When there's a tradeoff (rerank depth, chunk size, RRF k), name both sides and let me choose. Don't pick silently.
Flag when a change would invalidate an existing measurement.
Never
Add LangChain, LlamaIndex, or any orchestration framework. Raw SDK only.
Add anything from the non-goals list in docs/SPEC.md without telling me it's out of scope first.
Invent, estimate, or placeholder a metric. Numbers come from make eval.
Suggest local LLM hosting, quantization, or GPU serving.
Touch web/ before Phase 1's definition of done is checked.

Environment
MacBook M3 only. device = "mps". PYTORCH_ENABLE_MPS_FALLBACK=1.
The RTX 3050 is not used — measurement consistency matters more than the marginal speedup. Don't suggest a CUDA path.
Postgres + pgvector local.
BAAI/bge-small-en-v1.5 (bi-encoder), cross-encoder/ms-marco-MiniLM-L-6-v2.
Agent LLM via API. Local models are for embedding/reranking only.

Invariants
make eval regenerates every number in results/ from a clean checkout. If it can't, the number doesn't exist.
eval/qrels.jsonl is append-mostly. Changing an existing grade requires a note in eval/CHANGELOG.md explaining why.
Prompts live in prompts/ with a version string. Changing one requires re-running the agent eval before merge.
Retrieval variants are selectable by flag (dense | bm25 | hybrid | reranked) through one code path, not four forks. The API exposes the same flag.
Agent iteration cap enforced in code, never only in the prompt.
Tools return structured "no results" records. They never raise into the loop.
Phase 2 reports both local and deployed p95. Never quote only the fast one.

Ship-fast rules
Terminal-first. No frontend until Phase 1 is done.
Abstract-only embedding in v1. Section chunking is an experiment, not a prerequisite.
Hardcode config until it hurts. One config.py, no settings framework.
Tests cover metrics and retrieval correctness. Skip tests for route handlers.
Blocked >30 min on environment setup: ask for the workaround and move on. Environment yak-shaving is not the learning surface.

Definition of done
Phase 1 (weeks 1–4) — gate for everything else
40 queries graded in qrels.jsonl, self-agreement reported
Ablation table (dense / bm25 / hybrid / +rerank@100 / +rerank@50)
Agent eval: 30 tasks, success rate, 4-way failure taxonomy
Cost per query, p95 latency, cache hit rate documented
README with architecture diagram and results tables
Terminal demo runs in under 60s from clean checkout
Phase 2 (weeks 5–6)
Search UI with mode toggle; results reorder live, per-mode latency shown
Agent trace streamed over SSE
Static results page rendering the ablation table and failure taxonomy
Rate limiting on the agent endpoint before deploy
Deployed p95 measured and reported alongside local

Do not add features past this line.

Interview readiness check
Before calling this done, I should be able to answer unaided:

Why two-stage retrieval? What does a cross-encoder do that a bi-encoder can't?
Why did BM25 beat dense retrieval on some queries? Which ones, and why?
What is DCG, what's the ideal-DCG normalizer, why graded relevance over binary?
Where does my agent fail most, and what would I change to fix it?
What's my cost per query, and what dominates it?
Why is deployed p95 worse than local, and what would I do about it?

If Claude wrote the code behind any of these answers, I've defeated the point.
