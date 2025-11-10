import sys
import os
from chroma_db_setup import get_chroma_client, get_embedding_function
try:
    from tools import ToolBox
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from tools import ToolBox

toolbox = ToolBox()

@toolbox.tool
def query_vector_db(query: str, n_results: int = 3):
    client = get_chroma_client()
    collection = client.get_collection(
        name='fantasy_football_articles',
        embedding_function=get_embedding_function()
    )

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    print(results)

    return [
        {"id": doc_id, "text": doc_text, "score": score}
        for doc_id, doc_text, score in zip(
            results["ids"][0], results["documents"][0], results["distances"][0]
        )
    ]
