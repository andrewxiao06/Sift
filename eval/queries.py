"""The 40 hand-picked eval queries, by category. See docs/SPEC.md section 5.1."""

CONCEPT_QUERIES = [
    "combining keyword search and AI search for better results",
    "checking if a database query actually answers the question",
    "an AI that searches step by step instead of answering right away",
    "using knowledge graphs to improve AI answers",
    "speeding up long-context RAG without losing accuracy",
    "catching wrong answers before they reach the user",
    "search that works well even in a language other than English",
    "why AI assistants make up sources that don't exist",
    "letting an AI decide when it has enough information to stop searching",
    "measuring how good a ranked list of results actually is",
]

NAMED_ENTITY_QUERIES = [
    "reciprocal rank fusion with cross-encoder reranking",
    "reference-free text-to-SQL answerability estimation",
    "MCTS-guided multi-hop reasoning for code repositories",
    "GraphRAG with synthetic QA supervision",
    "KV cache reuse for long-context RAG",
    "madhhab-aware retrieval for Arabic fiqh",
    "Boolean Query Language for structure-aware web retrieval",
    "rank-deviation quality metric for multi-answer retrieval",
    "outcome reward models for SQL verification",
    "hierarchical heterogeneous knowledge graph for enterprise QA",
]

DESCRIPTIVE_QUERIES = [
    "making language models cite their sources",
    "how does attention work in transformers?",
    "figuring out why a search result is wrong",
    "reducing the amount of text an AI agent has to read",
    "an AI research assistant that browses and inspects pages like a person",
    "detecting when an AI should say it doesn't know",
    "improving search results for a narrow, specialized topic area",
    "teaching a retrieval system using AI-generated questions instead of human labels",
    "verifying an AI's answer using deterministic rule checks, not another AI",
    "routing a question to the right specialized knowledge source",
]

COMPARATIVE_QUERIES = [
    "sparse vs dense retrieval tradeoffs",
    "graph-based RAG vs plain vector retrieval",
    "when reranking helps vs when it doesn't",
    "cross-encoder reranker accuracy vs latency tradeoff",
    "fine-tuned rerankers vs off-the-shelf ones on a new domain",
    "single-shot RAG vs an agent that searches iteratively",
    "LLM-as-judge verification vs deterministic rule-based verification",
    "nDCG vs simpler metrics like precision@k",
    "keyword search vs semantic search on exact terminology queries",
    "single-hop vs multi-hop retrieval for complex questions",
]

ALL_QUERIES = CONCEPT_QUERIES + NAMED_ENTITY_QUERIES + DESCRIPTIVE_QUERIES + COMPARATIVE_QUERIES
