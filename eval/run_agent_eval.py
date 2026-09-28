"""Runs every task in eval/agent_tasks.jsonl through the agent, extracts cited
arxiv_ids from the final answer, and saves raw results for grading.

Citation quality (is what got cited actually relevant) is graded separately,
after this run, the same way eval/qrels.jsonl was graded — see eval/CHANGELOG.md.

Usage: uv run python -m eval.run_agent_eval
"""

import json
import re
from pathlib import Path

from app.agent.loop import run_agent

TASKS_PATH = Path(__file__).parent / "agent_tasks.jsonl"
RESULTS_PATH = Path(__file__).parent.parent / "results" / "agent_eval_raw.json"

ARXIV_ID_PATTERN = re.compile(r"\b(\d{4}\.\d{4,5})\b")


def extract_cited_ids(answer_text: str) -> list[str]:
    if not answer_text:
        return []
    seen = []
    for match in ARXIV_ID_PATTERN.findall(answer_text):
        if match not in seen:
            seen.append(match)
    return seen


def main():
    tasks = [json.loads(line) for line in open(TASKS_PATH)]
    print(f"Running {len(tasks)} agent eval tasks...\n")

    results = []
    for i, task in enumerate(tasks, start=1):
        question = task["question"]
        print(f"[{i}/{len(tasks)}] {question[:70]}")

        result = run_agent(question)
        cited_ids = extract_cited_ids(result["answer"] or "")

        results.append({
            "question": question,
            "task_type": task["task_type"],
            "known_good_papers": task["known_good_papers"],
            "answer": result["answer"],
            "cited_ids": cited_ids,
            "trace": result["trace"],
            "total_tokens": result["total_tokens"],
            "total_latency": result["total_latency"],
            "iterations_used": result["iterations_used"],
            "incomplete": result.get("incomplete", False),
        })

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nWrote {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
