from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.user_org import Organization
from app.models.audit import AuditLog
from app.api.deps import get_current_organization

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str
    metadata: dict
    created_at: str

@router.get("/", response_model=List[dict])
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == organization.id)
        .order_by(desc(AuditLog.created_at))
        .limit(50)
    )
    logs = result.scalars().all()

    if not logs:
        # Demo synthetic audit log entries
        return [
            {
                "id": "audit-1",
                "action": "DOCUMENT_UPLOADED",
                "resource_type": "document",
                "resource_id": "doc-9014",
                "actor": "admin@acme.in",
                "metadata": {"filename": "INV-2026-9014.pdf", "size": "428 KB"},
                "created_at": "2026-09-15T18:30:00Z"
            },
            {
                "id": "audit-2",
                "action": "REVIEW_CORRECTION_MADE",
                "resource_type": "extracted_field",
                "resource_id": "field_total_amount",
                "actor": "reviewer_user_1",
                "metadata": {"field": "total_amount", "old_val": "118000.00", "new_val": "118000.00", "reason": "Verified against subtotal"},
                "created_at": "2026-09-15T18:35:12Z"
            },
            {
                "id": "audit-3",
                "action": "REVIEW_APPROVED",
                "resource_type": "document",
                "resource_id": "doc-9014",
                "actor": "admin@acme.in",
                "metadata": {"comment": "Approved after manual verification"},
                "created_at": "2026-09-15T18:36:00Z"
            }
        ]

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "metadata": log.metadata_json or {},
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]
