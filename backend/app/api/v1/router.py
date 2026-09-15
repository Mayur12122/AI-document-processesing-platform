from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    documents,
    jobs,
    extraction,
    review,
    search,
    analytics,
    audit,
    evaluation
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Processing Jobs"])
api_router.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])
api_router.include_router(review.router, prefix="/review", tags=["Human Review Queue"])
api_router.include_router(search.router, prefix="/search", tags=["Hybrid Search & QA"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Cost"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Model Evaluation"])
