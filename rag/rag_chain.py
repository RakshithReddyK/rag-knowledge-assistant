from typing import List

from .vectorstore import VectorStore
from .llm import LLMClient
from .config import TOP_K


SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based ONLY on the provided context. "
    "If the answer is not in the context, say you don't know. Be concise and factual."
)


class RAGPipeline:
    def __init__(self):
        self.vs = VectorStore()
        self.llm = LLMClient()

    def _format_context(self, documents: List[str], metadatas: List[dict]) -> str:
        chunks = []
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source", "unknown")
            chunks.append(f"[Source: {source}]\n{doc}")
        return "\n\n---\n\n".join(chunks)

    def answer(self, question: str) -> dict:
        results = self.vs.query(question, top_k=TOP_K)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return {
                "answer": "I could not find relevant information in the indexed documents.",
                "context": [],
            }

        context_str = self._format_context(docs, metas)

        user_prompt = (
            f"Question: {question}\n\n"
            f"Context:\n{context_str}\n\n"
            "Answer using ONLY this context."
        )

        answer = self.llm.generate(
            system_prompt=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return {
            "answer": answer,
            "context": [
                {"text": d, "metadata": m} for d, m in zip(docs, metas)
            ],
        }
