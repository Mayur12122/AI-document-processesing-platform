from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.models.base import BaseModel

class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    embedding = Column(Vector(384), nullable=True) # 384 dimensions for all-MiniLM-L6-v2 or local default

class AnomalySignal(BaseModel):
    __tablename__ = "anomaly_signals"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type = Column(String, nullable=False)
    severity = Column(String, default="MEDIUM", nullable=False) # LOW | MEDIUM | HIGH
    message = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
