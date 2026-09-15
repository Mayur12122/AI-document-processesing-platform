from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.user_org import Organization
from app.models.job import ProcessingJob, ProcessingStep
from app.api.deps import get_current_organization

router = APIRouter()

class StepResponse(BaseModel):
    stage: str
    status: str
    duration_ms: float

class JobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    current_stage: str
    error_message: Optional[str]
    input_tokens: int
    output_tokens: int
    cost_estimate: float
    steps: List[StepResponse] = []

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    job_uuid = uuid.UUID(job_id)
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.id == job_uuid)
        .where(ProcessingJob.organization_id == organization.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    steps_res = await db.execute(
        select(ProcessingStep).where(ProcessingStep.job_id == job.id).order_by(ProcessingStep.created_at)
    )
    steps = steps_res.scalars().all()

    return JobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        status=job.status,
        current_stage=job.current_stage,
        error_message=job.error_message,
        input_tokens=job.input_tokens,
        output_tokens=job.output_tokens,
        cost_estimate=job.cost_estimate,
        steps=[
            StepResponse(stage=s.stage, status=s.status, duration_ms=s.duration_ms)
            for s in steps
        ]
    )
