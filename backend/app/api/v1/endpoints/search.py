from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.models.user_org import Organization
from app.services.search_service import search_service
from app.api.deps import get_current_organization

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    doc_type: Optional[str] = None
    top_k: int = 5

class Citation(BaseModel):
    document_id: str
    document_title: str
    page_number: int
    snippet: str

class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer: str
    citations: List[Citation] = []

@router.post("/", response_model=List[dict])
async def search_documents(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    return await search_service.hybrid_search(
        query=req.query,
        organization_id=organization.id,
        db=db,
        top_k=req.top_k,
        doc_type=req.doc_type
    )

@router.post("/ask", response_model=QAResponse)
async def ask_document_question(
    req: QARequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization)
):
    res = await search_service.ask_question(
        query=req.question,
        organization_id=organization.id,
        db=db
    )
    return QAResponse(
        answer=res["answer"],
        citations=[Citation(**c) for c in res["citations"]]
    )
