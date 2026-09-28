"""MCP server exposing Sift's retrieval tools to any MCP-compatible client
(Claude Desktop, Claude Code, claude.ai). Wraps the same tool functions the
in-repo agent (app/agent/loop.py) uses via app/agent/tools.py — no separate
retrieval logic lives here.

Run with: uv run python app/mcp_server.py
"""

from mcp.server.mcpserver import MCPServer

from app.agent.tools import compare_papers, get_paper, search_papers

mcp = MCPServer("sift")


@mcp.tool()
def search(query: str, k: int = 10) -> dict:
    """Search the Sift arXiv corpus (cs.IR / cs.CL) and return the top-k most
    relevant papers, using hybrid retrieval with cross-encoder reranking."""
    return search_papers(query, k)


@mcp.tool()
def paper(arxiv_id: str) -> dict:
    """Fetch the full structured record for a single paper by its arXiv id."""
    return get_paper(arxiv_id)


@mcp.tool()
def compare(arxiv_ids: list[str], dimension: str) -> dict:
    """Compare up to 5 papers along a given dimension, e.g. methodology or results."""
    return compare_papers(arxiv_ids, dimension)


if __name__ == "__main__":
    mcp.run()
