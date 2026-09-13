# eval/qrels.jsonl changelog

## 2026-09-11 — removed 14 grades for "an AI that searches step by step instead of answering right away"

All 14 candidates for this query had been graded 0. The grader (Andrew) did not
notice partway through that the displayed query text had changed to this one
(from the prior query), so these grades don't reflect real judgment against
this query's intent — they're not a legitimate "everything is irrelevant"
result. Removed rather than kept as-is. Re-grading for this query is pending.

## 2026-09-11 — removed 45 grades for "checking if a database query actually answers the question"

Every candidate had been graded 0, including several papers (TraceSQL,
"Business Truth not SQL Accuracy", "Never the Number", "Trace Integrity for
LLM Data Agents") that are near-verbatim matches for this query's intent
(text-to-SQL answerability/verification). A cross-check against an
independently-graded second set (eval/qrels_claude.jsonl) flagged this as a
likely systematic grading error rather than genuine judgment, probably the
same query-tracking issue that hit the next query. Removed; re-grading
pending.

## 2026-09-11 — added 1,381 LLM-graded pairs for the remaining 37 queries

After hand-grading and cross-checking 2 queries against an independent LLM
grading pass (see eval/qrels_claude.jsonl), Andrew decided the sample was
large enough to establish calibration and had Claude grade the remaining 37
queries directly, rather than hand-grading all 40. Grading was done by 6
parallel sub-agents, each applying the same 0-3 rubric (restate query intent,
compare against the abstract's stated problem/contribution). Grade
distribution: 632 zeros, 413 ones, 204 twos, 132 threes. No duplicate
(query, paper_id) pairs. This is a deliberate, documented methodology choice
— not silent automation — see the interview-readiness note: the grading
process itself (calibration via inter-annotator comparison, then delegated
bulk grading) is the defensible story, not a claim that all 1,423 pairs were
graded by hand.
