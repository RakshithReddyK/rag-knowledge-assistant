import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings

from .config import CHROMA_DIR
from .embeddings import EmbeddingModel


class VectorStore:
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[Union[str, Path]] = None,
        embedder: Optional[Any] = None,
    ):
        """
        Args:
            collection_name: Chroma collection to read/write.
            persist_directory: Where Chroma persists its files. Defaults to
                the app's configured ``CHROMA_DIR``; override in tests to
                point at a temporary directory instead of the real store.
            embedder: Object exposing ``.encode(texts)``. Defaults to the
                real ``EmbeddingModel``; override in tests to avoid loading
                the sentence-transformers model.
        """
        self.embedder = embedder if embedder is not None else EmbeddingModel()
        self.persist_directory = Path(persist_directory) if persist_directory else CHROMA_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(allow_reset=True)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        embeddings = self.embedder.encode(texts)
        ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def query(self, query: str, top_k: int = 5):
        query_embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        return results
