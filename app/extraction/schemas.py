"""Pydantic models validating data shapes as they move between the DB, tools, and the agent."""

from pydantic import BaseModel


class Paper(BaseModel):
    id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    pdf_url: str
