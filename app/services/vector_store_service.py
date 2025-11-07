"""Vector database service for semantic search using FAISS."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import AnthropicEmbeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings and semantic search."""

    def __init__(self, collection_name: str) -> None:
        """
        Initialize vector store for a collection.

        Args:
            collection_name: Name of the collection to create embeddings for
        """
        self.collection_name = collection_name
        self.vector_store_path = Path(settings.LOCAL_STORAGE_PATH) / "vectors" / collection_name
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.embeddings = self._get_embeddings()
        self.vector_store: Optional[FAISS] = None

    def _get_embeddings(self) -> Any:
        """Get embeddings model based on AI provider configuration."""
        if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY,
            )
        elif settings.AI_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            # Anthropic doesn't provide embeddings directly, use OpenAI as fallback
            if settings.OPENAI_API_KEY:
                logger.info("Using OpenAI embeddings as fallback for Anthropic")
                return OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=settings.OPENAI_API_KEY,
                )
            raise ValueError("OpenAI API key required for embeddings")
        else:
            raise ValueError("AI provider not configured properly")

    async def load_or_create(self) -> None:
        """Load existing vector store or create new one."""
        index_path = self.vector_store_path / "index.faiss"

        if index_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info(f"Loaded vector store for collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {str(e)}")
                self.vector_store = None

        if not self.vector_store:
            logger.info(f"Creating new vector store for collection: {self.collection_name}")
            # Create empty vector store
            self.vector_store = FAISS.from_texts(
                texts=[""],
                embedding=self.embeddings,
                metadatas=[{"id": "init"}],
            )

    async def add_documents(
        self, documents: List[Dict[str, Any]], id_key: str = "id"
    ) -> None:
        """
        Add or update documents in the vector store.

        Args:
            documents: List of document dictionaries to embed
            id_key: Key to use as document ID
        """
        if not self.vector_store:
            await self.load_or_create()

        # Convert documents to LangChain Document format
        docs = []
        for doc in documents:
            doc_id = doc.get(id_key, "")

            # Create text content from document fields
            text_parts = []
            for key, value in doc.items():
                if isinstance(value, (str, int, float, bool)):
                    text_parts.append(f"{key}: {value}")

            text = " | ".join(text_parts)

            docs.append(
                Document(
                    page_content=text,
                    metadata={"id": doc_id, "collection": self.collection_name},
                )
            )

        if docs:
            # Add documents to vector store
            if self.vector_store:
                self.vector_store.add_documents(docs)
                # Save to disk
                self.vector_store.save_local(str(self.vector_store_path))
                logger.info(f"Added {len(docs)} documents to vector store")

    async def remove_documents(self, document_ids: List[str]) -> None:
        """
        Remove documents from vector store.

        Args:
            document_ids: List of document IDs to remove
        """
        # FAISS doesn't support deletion efficiently, would need to rebuild
        # For production, consider using Qdrant which supports deletion
        logger.warning("Document deletion requires vector store rebuild for FAISS")

    async def search(
        self, query: str, k: int = 5, score_threshold: float = 0.0
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform semantic search in the vector store.

        Args:
            query: Search query text
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of (document, score) tuples
        """
        if not self.vector_store:
            await self.load_or_create()

        if not self.vector_store:
            return []

        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(query, k=k)

        # Filter by score threshold and format results
        filtered_results = []
        for doc, score in results:
            # FAISS returns distance, convert to similarity (lower distance = higher similarity)
            similarity = 1.0 / (1.0 + score)

            if similarity >= score_threshold:
                filtered_results.append((doc.metadata, similarity))

        logger.info(f"Semantic search returned {len(filtered_results)} results for query: {query}")
        return filtered_results

    async def rebuild_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Rebuild the entire vector store from scratch.

        Args:
            documents: All documents to index
        """
        logger.info(f"Rebuilding vector store for collection: {self.collection_name}")

        # Delete existing store
        if self.vector_store_path.exists():
            import shutil
            shutil.rmtree(self.vector_store_path)
            self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Reset vector store
        self.vector_store = None
        await self.load_or_create()

        # Add all documents
        if documents:
            await self.add_documents(documents)
