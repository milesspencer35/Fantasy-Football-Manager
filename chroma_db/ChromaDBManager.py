
import chromadb
import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from typing import List
from .Article import Article
from datetime import datetime, timedelta
load_dotenv()

CHROMA_DB_API_KEY = os.getenv('CHROMA_DB_API_KEY')
CHROMA_DB_TENANT = os.getenv('CHROMA_DB_TENANT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class ChromaDBManager:
    def __init__(self):
        self.client = chromadb.CloudClient(
            api_key=CHROMA_DB_API_KEY,
            tenant=CHROMA_DB_TENANT,
            database='fantasy_football'
        )
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-small"
        )
        self.collection = self.client.get_or_create_collection(
            name="fantasy_football_articles",
            embedding_function=self.embedding_fn
        )

    def store_articles_in_vector_db(self, articles: List[Article]):
        """Add articles to Chroma collection."""
        print(f"\n{'=' * 60}")
        print(f"Storing {len(articles)} articles to ChromaDB...")
        print(f"{'=' * 60}\n")

        stored_count = 0
        skipped_count = 0
        error_count = 0

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] {article.title[:60]}...")

            try:

                # Check if document exists
                existing = self.collection.get(ids=[article.id])

                if len(existing['ids']) == 0:
                    self.collection.add(
                        documents=[article.content],
                        metadatas=[{
                            "title": article.title,
                            "url": article.url,
                            "source": article.source,
                            "date": article.date.isoformat()
                        }],
                        ids=[article.id]
                    )
                    print(f"  ✓ STORED")
                    stored_count += 1
                else:
                    print(f"  ⊝ SKIPPED (already exists)")
                    skipped_count += 1

            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                error_count += 1

        print(f"\n{'=' * 60}")
        print(f"Summary:")
        print(f"  Stored: {stored_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Errors: {error_count}")
        print(f"{'=' * 60}\n")

    def cleanup_old_articles(self, max_age_days=14):
        """Remove articles older than max_age_days from the database."""
        print(f"\nCleaning up articles older than {max_age_days} days...")

        try:
            # Get all documents
            all_docs = self.collection.get()

            if not all_docs['ids']:
                print("No documents in collection")
                return

            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            ids_to_delete = []

            for i, metadata in enumerate(all_docs['metadatas']):
                if 'date' in metadata:
                    article_date = datetime.fromisoformat(metadata['date'])
                    if article_date < cutoff_date:
                        ids_to_delete.append(all_docs['ids'][i])

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"✓ Deleted {len(ids_to_delete)} old articles")
            else:
                print("No old articles to delete")

        except Exception as e:
            print(f"Error during cleanup: {e}")

        