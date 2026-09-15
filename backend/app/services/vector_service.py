from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentPage
from app.models.vector import DocumentChunk
from app.providers.embedding_provider import LocalEmbeddingProvider

class VectorService:
    def __init__(self):
        self.embedding_provider = LocalEmbeddingProvider()

    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        words = text.split()
        if not words:
            return []
            
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))
            i += (chunk_size - overlap)
        return chunks

    async def index_document(self, document_id: Any, db: AsyncSession):
        page_res = await db.execute(select(DocumentPage).where(DocumentPage.document_id == document_id))
        pages = page_res.scalars().all()

        for page in pages:
            if not page.ocr_text:
                continue

            chunks = self.chunk_text(page.ocr_text)
            for idx, chunk_str in enumerate(chunks):
                vector = await self.embedding_provider.embed_text(chunk_str)
                chunk_obj = DocumentChunk(
                    document_id=document_id,
                    page_number=page.page_number,
                    chunk_index=idx,
                    chunk_text=chunk_str,
                    token_count=len(chunk_str.split()),
                    embedding=vector
                )
                db.add(chunk_obj)

        await db.commit()

vector_service = VectorService()
