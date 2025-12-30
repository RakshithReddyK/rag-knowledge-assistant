import os
import uuid
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings

from .config import CHROMA_DIR
from .embeddings import EmbeddingModel

class VectorStore:
    def __init__(self, collection_name: str = "documents"):
        self.embedder = EmbeddingModel()
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
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
