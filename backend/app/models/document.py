import enum
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    CLASSIFIED = "CLASSIFIED"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"
    BANK_STATEMENT = "bank_statement"
    INSURANCE_DOCUMENT = "insurance_document"
    GST_DOCUMENT = "gst_document"
    GOVERNMENT_FORM = "government_form"
    UNKNOWN = "unknown"

class Document(BaseModel):
    __tablename__ = "documents"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String, index=True, nullable=False)
    perceptual_hash = Column(String, nullable=True)
    
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.UNKNOWN, nullable=False, index=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    language = Column(String, default="en", nullable=False)
    
    storage_path = Column(String, nullable=False)
    current_version_number = Column(Integer, default=1, nullable=False)
    
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization = relationship("Organization", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", foreign_keys="[DocumentVersion.document_id]")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")
    review_tasks = relationship("ReviewTask", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    document = relationship("Document", back_populates="versions", foreign_keys=[document_id])

class DocumentPage(BaseModel):
    __tablename__ = "document_pages"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True)
    page_number = Column(Integer, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    height = Column(Integer, default=0, nullable=False)
    ocr_text = Column(Text, nullable=True)
    ocr_blocks_json = Column(JSON, nullable=True)  # Bounding boxes + word metadata
    image_storage_path = Column(String, nullable=True)

    document = relationship("Document", back_populates="pages")
