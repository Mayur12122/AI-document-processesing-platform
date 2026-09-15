from abc import ABC, abstractmethod
from typing import List
import math
import hashlib

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic 384-dimensional vector embedding generator using word hash projections.
    Provides real vector similarity math for pgvector index without external API dependencies.
    """
    DIM = 384

    async def embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.DIM
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Deterministic hash to dimension index
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % self.DIM
            val = (h % 100) / 100.0
            vec[idx] += val

        # Normalize vector to unit length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]
