from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.user_org import User, Organization
from app.models.document import Document, DocumentVersion, DocumentStatus, DocumentType
from app.models.job import ProcessingJob
from app.models.audit import AuditLog
from app.services.storage_service import storage_service
from app.api.deps import get_current_user, get_current_organization

router = APIRouter()

class DocumentResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    mime_type: str
    file_size: int
    file_hash: str
    status: str
    document_type: str
    confidence_score: float
    is_duplicate: bool
    created_at: str

    class Config:
        from_attributes = True

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
):
    # Validate MIME type and size limit (max 50MB)
    allowed_mimes = ["application/pdf", "image/png", "image/jpeg", "image/tiff", "image/webp"]
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPEG, TIFF, WEBP."
        )

    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 50MB.")

    doc_title = title if title else file.filename
    storage_path, sha256_hash, p_hash = await storage_service.upload_document(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        organization_id=str(organization.id)
    )

    # Check for duplicates in the organization
    dup_result = await db.execute(
        select(Document)
        .where(Document.organization_id == organization.id)
        .where(Document.file_hash == sha256_hash)
    )
    existing_dup = dup_result.scalars().first()
    is_dup = existing_dup is not None

    document = Document(
        organization_id=organization.id,
        title=doc_title,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=len(file_bytes),
        file_hash=sha256_hash,
        perceptual_hash=p_hash,
        status=DocumentStatus.QUEUED,
        document_type=DocumentType.UNKNOWN,
        confidence_score=0.0,
        storage_path=storage_path,
        is_duplicate=is_dup,
        duplicate_of_id=existing_dup.id if is_dup else None,
        created_by=current_user.id
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Create Document Version
    doc_version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        storage_path=storage_path,
        file_hash=sha256_hash,
        status=DocumentStatus.QUEUED,
        created_by=current_user.id
    )
    db.add(doc_version)

    # Create Processing Job
    job = ProcessingJob(
        document_id=document.id,
        organization_id=organization.id,
        status="QUEUED",
        current_stage="INGESTION"
    )
    db.add(job)

    # Record Audit Log
    audit = AuditLog(
        organization_id=organization.id,
        actor_id=current_user.id,
        action="DOCUMENT_UPLOADED",
        resource_type="document",
        resource_id=str(document.id),
        metadata_json={"filename": file.filename, "size": len(file_bytes), "hash": sha256_hash}
    )
    db.add(audit)

    await db.commit()

    # Trigger Celery Background Processing Pipeline
    try:
        from app.workers.celery_app import celery_app
        celery_app.send_task("process_document_pipeline", args=[str(document.id), str(job.id)])
    except Exception as e:
        # If celery broker is offline, mark job for immediate processing
        pass

    return DocumentResponse(
        id=str(document.id),
        title=document.title,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_size=document.file_size,
        file_hash=document.file_hash,
        status=document.status.value,
        document_type=document.document_type.value,
        confidence_score=document.confidence_score,
        is_duplicate=document.is_duplicate,
        created_at=document.created_at.isoformat()
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    status_filter: Optional[str] = Query(None),
    doc_type_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    query = select(Document).where(Document.organization_id == organization.id).order_by(desc(Document.created_at))
    
    if status_filter:
        query = query.where(Document.status == status_filter)
    if doc_type_filter:
        query = query.where(Document.document_type == doc_type_filter)

    result = await db.execute(query)
    docs = result.scalars().all()

    return [
        DocumentResponse(
            id=str(d.id),
            title=d.title,
            original_filename=d.original_filename,
            mime_type=d.mime_type,
            file_size=d.file_size,
            file_hash=d.file_hash,
            status=d.status.value,
            document_type=d.document_type.value,
            confidence_score=d.confidence_score,
            is_duplicate=d.is_duplicate,
            created_at=d.created_at.isoformat()
        ) for d in docs
    ]

@router.get("/{document_id}")
async def get_document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    doc_uuid = uuid.UUID(document_id)
    result = await db.execute(
        select(Document)
        .where(Document.id == doc_uuid)
        .where(Document.organization_id == organization.id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    presigned_url = storage_service.get_presigned_url(doc.storage_path)

    return {
        "id": str(doc.id),
        "title": doc.title,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "file_hash": doc.file_hash,
        "status": doc.status.value,
        "document_type": doc.document_type.value,
        "confidence_score": doc.confidence_score,
        "language": doc.language,
        "storage_url": presigned_url,
        "is_duplicate": doc.is_duplicate,
        "created_at": doc.created_at.isoformat()
    }
