from app.models.encoders import embed
from app.models.db import get_connection

#1) fetch papers that need embeddings

def fetch_papers_without_embeddings() -> list[dict]:
    """Fetches papers that do not have embeddings yet."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, abstract FROM papers WHERE embedding IS NULL;")
        rows = cur.fetchall()
    conn.close()
    return [{"id": row[0], "abstract": row[1]} for row in rows]


#2 write each vector back   

def write_embeddings_to_db(paper_ids: list[int], embeddings: list[list[float]]) -> None:
    """Writes embeddings back to the database for the given paper IDs."""
    conn = get_connection()
    with conn.cursor() as cur:
        for paper_id, embedding in zip(paper_ids, embeddings):
            cur.execute(
                "UPDATE papers SET embedding = %s WHERE id = %s;",
                (embedding, paper_id),
            )
        conn.commit()
    conn.close()

#3 commit every N rows or once per batch, and create the batch

def process_and_write_embeddings(batch_size: int = 32) -> None:
    """Fetches papers without embeddings, computes embeddings in batches, and writes them back to the database."""
    papers = fetch_papers_without_embeddings()
    total_papers = len(papers)
    print(f"Total papers without embeddings: {total_papers}")

    for i in range(0, total_papers, batch_size):
        batch = papers[i:i + batch_size]
        paper_ids = [paper["id"] for paper in batch]
        abstracts = [paper["abstract"] for paper in batch]

        embeddings = embed(abstracts)
        write_embeddings_to_db(paper_ids, embeddings)
        print(f"Processed and wrote embeddings for papers {i + 1} to {min(i + batch_size, total_papers)}")


#wrap as a function that can be called from command line or script

def embed_and_write_all_embeddings(batch_size: int = 32) -> None:
    """Main function to embed and write all embeddings for papers without embeddings."""
    process_and_write_embeddings(batch_size)

