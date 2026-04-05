"""fastembed ResourceEmbedder — replaces sentence-transformers (no PyTorch needed).

Uses BAAI/bge-small-en-v1.5 (same dimensionality as all-MiniLM-L6-v2: 384-dim).
Singleton loaded at first use.
"""
import asyncio
import numpy as np
from typing import ClassVar

MODEL_NAME = "BAAI/bge-small-en-v1.5"


class ResourceEmbedder:
    _model: ClassVar = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            from fastembed import TextEmbedding
            cls._model = TextEmbedding(model_name=MODEL_NAME)

    def _embed_sync(self, texts: list[str]) -> np.ndarray:
        self._load()
        embeddings = list(self._model.embed(texts))
        return np.array(embeddings, dtype=np.float32)

    async def embed(self, texts: list[str]) -> np.ndarray:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    async def embed_single(self, text: str) -> np.ndarray:
        result = await self.embed([text])
        return result[0]
