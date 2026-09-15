# Agent manual stress tests

Ad hoc tests of `run_agent()` end to end, before building the formal Week 4 agent eval
(`eval/agent_tasks.jsonl`, 30 tasks, success rate, failure taxonomy). These are qualitative
checks of specific behaviors, not a scored benchmark — see `docs/SPEC.md` §7-8 for what the
real eval will measure.

Model: `claude-sonnet-5`. System prompt: `prompts/agent_system_v1.md`.

---

## Test 1 — normal case: a well-covered concept question

**Query:** "What is reciprocal rank fusion and why is it used in hybrid retrieval?"

**Trace:** 3× `search_papers` calls (query refined each time), 0 errors.

**Result:** Correct, well-grounded answer. Explained the RRF formula correctly, explained why
rank-based fusion avoids the BM25-vs-cosine score-scale mismatch problem, and cited 3 real
papers from the corpus by arxiv_id (SciRet, EAHR, DESA) with accurate one-line summaries of
each paper's relevance. No hallucinated citations — all three arxiv_ids are real corpus papers.

**Finding:** The core RAG loop (search → read → synthesize → cite) works as intended.

---

## Test 2 — off-topic query (outside the corpus domain entirely)

**Query:** "What is the best recipe for a chocolate souffle?"

**Trace:** 0 tool calls.

**Result:** Declined cleanly: *"That's outside what I can help with—my tools search an
academic paper corpus on information retrieval and NLP topics, not cooking recipes... I'd
rather not guess."* Offered a relevant pivot (NLP research on recipe generation) instead of a
flat refusal.

**Finding, worth a design decision:** the model declined **without calling `search_papers`
even once** — it judged topic fit from the question alone rather than confirming via a real
(empty) search. This matches the system prompt's "say so clearly instead of guessing," but it
means the model's judgment of "is this in-domain" is untested against the actual corpus. A
borderline query might get wrongly declined without ever getting a chance to search. Worth
deciding: is trusting the model's own topic judgment here acceptable, or should the prompt
require at least one search attempt before declining?

---

## Test 3 — plausible in-domain query with weak/no real coverage

**Query:** "How does federated learning improve differential privacy guarantees in
recommendation systems?"

**Trace:** 4× `search_papers` calls, each with a differently-phrased query (query refinement
in action), 0 errors.

**Result:** Honestly reported no strong match: *"I wasn't able to find papers that directly
address this intersection."* Offered the closest tangential match (PriCoRec, a
privacy-aware recommender paper) rather than forcing an answer or hallucinating a paper that
doesn't exist.

**Finding:** This is the strongest evidence so far that the agent won't hallucinate when
retrieval genuinely comes up short — it degrades to "here's the closest thing I found,
clearly labeled as not a direct match" rather than inventing a confident wrong answer. Also
shows real query-refinement behavior: 4 distinct rephrasings attempted before giving up.

---

## Test 4 — forcing `compare_papers` over its 5-id cap

**Query:** "Compare these 6 papers on their methodology: [6 real arxiv_ids]"

**Trace:** 6× `get_paper` calls (one per id) — **`compare_papers` was never called.**

**Result:** The model worked around the tool's stated 5-id limit (visible in its
`TOOL_DEFINITIONS` description) by fetching each paper individually via `get_paper` instead,
then synthesizing the comparison itself in its final answer. The comparison was still
substantively correct.

**Finding — the retry/validation-error path for `compare_papers` is still functionally
untested in the live agent loop.** The model is well-behaved enough to avoid the tool
limit rather than hit it, so `loop.py`'s `except Exception` branch and `tool_failure_counts`
logic have never actually fired end to end. Confirmed separately via a direct unit call that
`compare_papers(arxiv_ids=[7 ids], ...)` does correctly raise `ValueError: compare_papers
accepts at most 5 arxiv_ids.` — so the validation itself works, but the loop's *handling* of
that error (building the `is_error` tool_result, incrementing `tool_failure_counts`,
eventually telling the model to stop retrying) has not been observed in a real run. To
actually exercise this, either force a tool call directly (bypassing the model) or find a
prompt that reliably makes the model call `compare_papers` with too many ids instead of
routing around it.

---

## Test 5 — `get_paper` on a nonexistent arxiv_id

**Query:** "Can you get me the details of the paper with arxiv id 9999.99999?"

**Trace:** 1× `get_paper` call, returned `{"error": "No paper found with arxiv_id
9999.99999."}` — no exception raised.

**Result:** Handled gracefully: explained the ID wasn't found, and added (correct) reasoning
about why — arXiv IDs don't use a "9999" year/month prefix — then asked for a real ID or
topic instead.

**Finding:** Confirms the "explicit no-results record, never an exception" requirement works
as designed for `get_paper`. The extra reasoning about arXiv ID conventions is the model's own
general knowledge, not something retrieved — worth noting as a minor distinction (correct here,
but a reminder that the model will readily add unretrieved context on top of tool results).

---

## Summary / open items

- Core loop, citation grounding, honest "no good match" degradation, and empty-result
  handling all work as designed.
- **Not yet tested**: the actual retry-then-give-up path (`tool_failure_counts > 2`) in a live
  run — the model has been too well-behaved to trigger it. Needs a more adversarial test.
- **Open design question**: should the agent be required to attempt at least one search before
  declining an apparently off-topic question, rather than trusting its own judgment?
- Token usage/cost was not measured in these tests — still pending the token-tracking work.
