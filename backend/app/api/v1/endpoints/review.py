from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.user_org import User, Organization
from app.models.document import Document, DocumentStatus, DocumentPage
from app.models.review import ReviewTask, ReviewAction
from app.models.extraction import Extraction, ExtractedField, ValidationResult
from app.models.audit import AuditLog
from app.api.deps import get_current_user, get_current_organization

router = APIRouter()

class ReviewTaskResponse(BaseModel):
    id: str
    document_id: str
    title: str
    document_type: str
    confidence_score: float
    status: str
    priority: str
    created_at: str

class CorrectionRequest(BaseModel):
    field_name: str
    corrected_value: str
    reason: Optional[str] = "Human reviewer correction"

class DecisionRequest(BaseModel):
    comment: Optional[str] = None

@router.get("/queue", response_model=List[ReviewTaskResponse])
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    result = await db.execute(
        select(ReviewTask, Document)
        .join(Document, ReviewTask.document_id == Document.id)
        .where(ReviewTask.organization_id == organization.id)
        .where(ReviewTask.status.in_(["PENDING", "IN_PROGRESS"]))
        .order_by(desc(ReviewTask.created_at))
    )
    rows = result.all()

    return [
        ReviewTaskResponse(
            id=str(task.id),
            document_id=str(doc.id),
            title=doc.title,
            document_type=doc.document_type.value,
            confidence_score=doc.confidence_score,
            status=task.status,
            priority=task.priority,
            created_at=task.created_at.isoformat()
        )
        for task, doc in rows
    ]

@router.get("/{document_id}")
async def get_review_detail(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    doc_uuid = uuid.UUID(document_id)
    doc_res = await db.execute(
        select(Document)
        .where(Document.id == doc_uuid)
        .where(Document.organization_id == organization.id)
    )
    doc = doc_res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Fetch extraction
    ext_res = await db.execute(select(Extraction).where(Extraction.document_id == doc.id))
    extraction = ext_res.scalars().first()

    fields_data = []
    validations_data = []

    if extraction:
        fields_res = await db.execute(select(ExtractedField).where(ExtractedField.extraction_id == extraction.id))
        fields = fields_res.scalars().all()
        fields_data = [
            {
                "id": str(f.id),
                "field_name": f.field_name,
                "field_value": f.field_value,
                "confidence": f.confidence,
                "page_number": f.page_number,
                "bounding_box": f.bounding_box_json,
                "is_human_corrected": f.is_human_corrected,
                "original_ai_value": f.original_ai_value
            }
            for f in fields
        ]

        val_res = await db.execute(select(ValidationResult).where(ValidationResult.extraction_id == extraction.id))
        validations = val_res.scalars().all()
        validations_data = [
            {
                "rule_name": v.rule_name,
                "field_name": v.field_name,
                "status": v.status,
                "message": v.message
            }
            for v in validations
        ]

    # Fetch OCR text
    page_res = await db.execute(select(DocumentPage).where(DocumentPage.document_id == doc.id).where(DocumentPage.page_number == 1))
    page = page_res.scalars().first()

    return {
        "document_id": str(doc.id),
        "title": doc.title,
        "document_type": doc.document_type.value,
        "confidence_score": doc.confidence_score,
        "status": doc.status.value,
        "storage_path": doc.storage_path,
        "ocr_text": page.ocr_text if page else "",
        "ocr_blocks": page.ocr_blocks_json if page else [],
        "fields": fields_data,
        "validations": validations_data,
        "extraction_json": extraction.extraction_json if extraction else {}
    }

@router.post("/{document_id}/correct")
async def correct_field(
    document_id: str,
    req: CorrectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
):
    doc_uuid = uuid.UUID(document_id)
    ext_res = await db.execute(select(Extraction).where(Extraction.document_id == doc_uuid))
    extraction = ext_res.scalars().first()
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found for document")

    field_res = await db.execute(
        select(ExtractedField)
        .where(ExtractedField.extraction_id == extraction.id)
        .where(ExtractedField.field_name == req.field_name)
    )
    field = field_res.scalars().first()

    if not field:
        field = ExtractedField(
            extraction_id=extraction.id,
            field_name=req.field_name,
            field_value=req.corrected_value,
            confidence=1.0,
            is_human_corrected=True,
            original_ai_value="",
            corrected_by=current_user.id,
            corrected_at=datetime.utcnow(),
            change_reason=req.reason
        )
        db.add(field)
    else:
        if not field.is_human_corrected:
            field.original_ai_value = field.field_value
        field.field_value = req.corrected_value
        field.confidence = 1.0
        field.is_human_corrected = True
        field.corrected_by = current_user.id
        field.corrected_at = datetime.utcnow()
        field.change_reason = req.reason

    # Update extraction JSON dictionary
    ext_json = dict(extraction.extraction_json)
    ext_json[req.field_name] = req.corrected_value
    extraction.extraction_json = ext_json

    await db.commit()
    return {"status": "success", "field_name": req.field_name, "new_value": req.corrected_value}

@router.post("/{document_id}/approve")
async def approve_document(
    document_id: str,
    req: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
):
    doc_uuid = uuid.UUID(document_id)
    doc_res = await db.execute(
        select(Document)
        .where(Document.id == doc_uuid)
        .where(Document.organization_id == organization.id)
    )
    doc = doc_res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = DocumentStatus.COMPLETED

    task_res = await db.execute(select(ReviewTask).where(ReviewTask.document_id == doc.id))
    task = task_res.scalars().first()
    if task:
        task.status = "APPROVED"
        task.completed_at = datetime.utcnow()

        action = ReviewAction(
            review_task_id=task.id,
            actor_id=current_user.id,
            action_type="APPROVE",
            comment=req.comment
        )
        db.add(action)

    audit = AuditLog(
        organization_id=organization.id,
        actor_id=current_user.id,
        action="REVIEW_APPROVED",
        resource_type="document",
        resource_id=str(doc.id),
        metadata_json={"comment": req.comment}
    )
    db.add(audit)

    await db.commit()
    return {"status": "approved", "document_id": str(doc.id)}
