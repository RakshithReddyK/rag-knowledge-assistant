from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL_NAME

class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts, normalize: bool = True):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, normalize_embeddings=normalize)
        return embeddings.tolist()
