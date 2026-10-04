import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings

from .config import CHROMA_DIR


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
        if embedder is None:
            from .embeddings import EmbeddingModel
            embedder = EmbeddingModel()
        self.embedder = embedder
        self.persist_directory = Path(persist_directory) if persist_directory else CHROMA_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(allow_reset=True)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        if len(texts) != len(metadatas):
            raise ValueError("texts and metadatas must have the same length")
        if not texts:
            return
        embeddings = self.embedder.encode(texts)
        ids = [hashlib.sha256(
            f"{meta['source']}:{meta['chunk_index']}:{text}".encode()
        ).hexdigest() for text, meta in zip(texts, metadatas)]
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def replace_texts(self, texts, metadatas):
        """Upsert current chunks, then remove stale chunks after successful encoding.

        Run ingestion offline. This two-phase update is not atomic for concurrent readers.
        """
        self.add_texts(texts, metadatas)
        active = {hashlib.sha256(
            f"{meta['source']}:{meta['chunk_index']}:{text}".encode()
        ).hexdigest() for text, meta in zip(texts, metadatas)}
        stale = set(self.collection.get()["ids"]) - active
        if stale:
            self.collection.delete(ids=sorted(stale))

    def query(self, query: str, top_k: int = 5):
        if top_k < 1:
            raise ValueError("top_k must be positive")
        count = self.collection.count()
        if not count:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        query_embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, count)
        )
        return results
