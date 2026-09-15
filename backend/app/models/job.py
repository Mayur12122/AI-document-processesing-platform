from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class ProcessingJob(BaseModel):
    __tablename__ = "processing_jobs"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String, default="QUEUED", nullable=False, index=True)
    current_stage = Column(String, default="INGESTION", nullable=False)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    
    model_used = Column(String, default="local", nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    cost_estimate = Column(Float, default=0.0, nullable=False)

    document = relationship("Document", back_populates="jobs")
    steps = relationship("ProcessingStep", back_populates="job", cascade="all, delete-orphan")

class ProcessingStep(BaseModel):
    __tablename__ = "processing_steps"

    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    error_detail = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    job = relationship("ProcessingJob", back_populates="steps")
