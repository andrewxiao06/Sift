from app.models.db import get_connection
from app.models.encoders import embed

def dense_search(query: str, top_k: int = 10) -> list[dict]:
    """Returns top_k papers most similar to the query, by embedding cosine distance."""
        # 1. embed the query — remember embed() takes a list, returns a list
        # 2. grab your connection (get_connection())
        # 3. write a SQL query: SELECT ... FROM papers ORDER BY embedding <=> %s LIMIT %s
        #    - the <=> operator is pgvector's cosine distance
        #    - smaller distance = more similar, so ORDER BY ... ASC gets your best matches first
        # 4. execute it, passing the query vector and top_k as params
        # 5. fetch results, close the connection
        # 6. return them in whatever shape you want downstream (list of dicts? tuples?)

    query_embedding = embed([query])[0]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("Select id, arxiv_id, title, abstract FROM papers ORDER BY embedding <=> %s:: vector LIMIT %s", (query_embedding, top_k))
    results = cursor.fetchall()
    columns = [col.name for col in cursor.description]

    cursor.close()
    conn.close()

    return [dict(zip(columns, row)) for row in results]

    
    