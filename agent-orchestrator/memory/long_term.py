from __future__ import annotations

import os
from typing import List, Tuple

import faiss
import numpy as np
from sqlalchemy import select

from api.config import settings
from api.database import get_session
from api.models import LongTermMemory
from memory.embeddings import embed_texts, embedding_dimension


class LongTermMemoryStore:
    def __init__(self) -> None:
        self.index_path = settings.faiss_index_path
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> faiss.Index:
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        base_index = faiss.IndexFlatL2(embedding_dimension())
        return faiss.IndexIDMap(base_index)

    def _persist(self) -> None:
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)

    async def add_text(self, content: str, metadata: dict) -> int:
        vector = embed_texts([content])[0]
        async with get_session() as session:
            result = await session.execute(select(LongTermMemory).order_by(LongTermMemory.embedding_id.desc()).limit(1))
            last = result.scalar_one_or_none()
            next_id = 1 if last is None else last.embedding_id + 1
            memory = LongTermMemory(embedding_id=next_id, content=content, meta=metadata)
            session.add(memory)
            await session.commit()
        vector_array = np.array([vector], dtype=\"float32\")
        id_array = np.array([next_id], dtype=\"int64\")
        self.index.add_with_ids(vector_array, id_array)
        self._persist()
        return next_id

    async def search(self, query: str, k: int = 5) -> List[Tuple[LongTermMemory, float]]:
        vector = embed_texts([query])[0]
        if self.index.ntotal == 0:
            return []
        vector_array = np.array([vector], dtype=\"float32\")
        distances, ids = self.index.search(vector_array, k)
        id_list = [int(idx) for idx in ids[0] if idx != -1]
        if not id_list:
            return []
        async with get_session() as session:
            result = await session.execute(select(LongTermMemory).where(LongTermMemory.embedding_id.in_(id_list)))
            records = {record.embedding_id: record for record in result.scalars().all()}
        return [(records[idx], float(distances[0][pos])) for pos, idx in enumerate(id_list) if idx in records]
