import chromadb
import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()

CHROMA_DB_API_KEY = os.getenv('CHROMA_DB_API_KEY')
CHROMA_DB_TENANT = os.getenv('CHROMA_DB_TENANT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def get_chroma_client():
    return chromadb.CloudClient(
        api_key=CHROMA_DB_API_KEY,
        tenant=CHROMA_DB_TENANT,
        database='fantasy_football'
    )

def get_embedding_function():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )
