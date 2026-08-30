"""Hardcoded project config. No settings framework — see CLAUDE.md ship-fast rules."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://andrewxiao@localhost:5432/sift"
)

# arXiv corpus scope — see docs/SPEC.md section 4
ARXIV_CATEGORIES = ["cs.IR", "cs.CL"]
ARXIV_MAX_RESULTS = 2000
ARXIV_MONTHS_BACK = 24

# Models — see docs/SPEC.md section 3
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# MPS only — no CUDA path, see CLAUDE.md environment section
DEVICE = "mps"

# Retrieval defaults
DEFAULT_TOP_K = 10
RERANK_TOP_N = 100

# Agent
AGENT_MODEL = "claude-sonnet-5"
AGENT_MAX_ITERATIONS = 6

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
