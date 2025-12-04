import sys
import os
from chroma_db.ChromaDBManager import ChromaDBManager
try:
    from tools import ToolBox
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from tools import ToolBox

lineup_toolbox = ToolBox()

@lineup_toolbox.tool
def query_fantasy_football_db(query: str, n_results: int = 3):
    """
    Query the fantasy football articles database using semantic search.

    Searches a ChromaDB collection of fantasy football articles and returns
    the most relevant documents based on the query text using embedding-based
    similarity search.

    Args:
        query (str): The search query text to find relevant articles
        n_results (int, optional): Maximum number of results to return.
            Defaults to 3.

    Returns:
        list[dict]: A list of matching documents, where each dict contains:
            - id (str): The unique document identifier
            - text (str): The full document text content
            - score (float): The distance score (lower is more similar)

    Example:
        > results = query_fantasy_football_db("Drake Maye performance", n_results=5)
        > print(results[0]['text'][:100])
    """
    chroma_db_manager = ChromaDBManager()

    print(f"Querying fantasy football vector db: {query}, n_results: {n_results}")

    results = chroma_db_manager.collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    return [
        {"url": meta.get("url"), "text": doc_text, "score": score}
        for meta, doc_text, score in zip(
            results["metadatas"][0], results["documents"][0], results["distances"][0]
        )
    ]