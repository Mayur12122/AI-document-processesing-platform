from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Extraction(BaseModel):
    __tablename__ = "extractions"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id", ondelete="SET NULL"), nullable=True)
    
    document_type = Column(String, nullable=False)
    extraction_json = Column(JSON, nullable=False)
    raw_llm_response = Column(Text, nullable=True)
    confidence_overall = Column(Float, default=0.0, nullable=False)

    document = relationship("Document", back_populates="extractions")
    fields = relationship("ExtractedField", back_populates="extraction", cascade="all, delete-orphan")
    validations = relationship("ValidationResult", back_populates="extraction", cascade="all, delete-orphan")

class ExtractedField(BaseModel):
    __tablename__ = "extracted_fields"

    extraction_id = Column(UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String, nullable=False, index=True)
    field_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    bounding_box_json = Column(JSON, nullable=True) # [x, y, w, h] normalized 0..1000
    
    is_human_corrected = Column(Boolean, default=False, nullable=False)
    original_ai_value = Column(Text, nullable=True)
    corrected_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    corrected_at = Column(DateTime, nullable=True)
    change_reason = Column(Text, nullable=True)

    extraction = relationship("Extraction", back_populates="fields")

class ValidationResult(BaseModel):
    __tablename__ = "validation_results"

    extraction_id = Column(UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    status = Column(String, nullable=False)  # PASSED | WARNING | FAILED
    message = Column(Text, nullable=False)

    extraction = relationship("Extraction", back_populates="validations")
