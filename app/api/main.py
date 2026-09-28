"""Minimal local FastAPI server for the Sift frontend. Not part of the
measured Phase 1 deliverable — a visualization convenience, explicitly
scoped out of the phase gate at the user's request.

Run with: uv run uvicorn app.api.main:app --reload
Then open http://localhost:8000
"""

import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.loop import run_agent
from app.config import AGENT_MODELS, AGENT_MODES

app = FastAPI()

WEB_DIR = Path(__file__).parent.parent.parent / "web"
ARXIV_ID_PATTERN = re.compile(r"\b(\d{4}\.\d{4,5})\b")


class AskRequest(BaseModel):
    question: str
    model: Literal["haiku", "sonnet", "opus"] = "haiku"
    mode: Literal["fast", "detailed"] = "detailed"


def extract_papers_from_trace(trace: list[dict]) -> list[dict]:
    """Pulls every unique paper the agent actually saw during its run,
    from search_papers / get_paper / compare_papers tool results."""
    seen = {}
    for step in trace:
        result = step.get("result")
        if not isinstance(result, dict):
            continue

        candidates = []
        if "results" in result:  # search_papers
            candidates.extend(result["results"])
        if "papers" in result:  # compare_papers
            candidates.extend(result["papers"])
        if "arxiv_id" in result:  # get_paper
            candidates.append(result)

        for c in candidates:
            arxiv_id = c.get("arxiv_id")
            if arxiv_id and arxiv_id not in seen:
                seen[arxiv_id] = {"arxiv_id": arxiv_id, "title": c.get("title", arxiv_id)}

    return list(seen.values())


@app.post("/api/ask")
def ask(req: AskRequest):
    result = run_agent(
        req.question,
        max_iterations=AGENT_MODES[req.mode],
        model=AGENT_MODELS[req.model],
    )
    answer = result["answer"] or ""

    cited_ids = set(ARXIV_ID_PATTERN.findall(answer))
    seen_papers = extract_papers_from_trace(result["trace"])
    for p in seen_papers:
        p["cited"] = p["arxiv_id"] in cited_ids

    return {
        "question": req.question,
        "model": req.model,
        "mode": req.mode,
        "answer": answer,
        "papers": seen_papers,
        "iterations_used": result.get("iterations_used"),
        "total_tokens": result.get("total_tokens"),
        "total_latency": result.get("total_latency"),
        "incomplete": result.get("incomplete", False),
    }


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
