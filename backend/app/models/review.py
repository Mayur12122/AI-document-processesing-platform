from sqlalchemy import Column, String, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class ReviewTask(BaseModel):
    __tablename__ = "review_tasks"

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String, default="PENDING", nullable=False, index=True) # PENDING | IN_PROGRESS | APPROVED | REJECTED
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String, default="MEDIUM", nullable=False)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="review_tasks")
    actions = relationship("ReviewAction", back_populates="review_task", cascade="all, delete-orphan")

class ReviewAction(BaseModel):
    __tablename__ = "review_actions"

    review_task_id = Column(UUID(as_uuid=True), ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    action_type = Column(String, nullable=False) # APPROVE | REJECT | CORRECT | REPROCESS
    comment = Column(Text, nullable=True)
    changes_json = Column(JSON, nullable=True)

    review_task = relationship("ReviewTask", back_populates="actions")
