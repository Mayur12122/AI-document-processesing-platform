import asyncio
from app.workers.celery_app import celery_app
from app.pipelines.pipeline_engine import pipeline_engine
from app.core.logging import logger

@celery_app.task(name="process_document_pipeline")
def process_document_pipeline(document_id: str, job_id: str):
    logger.info(f"Celery worker received document processing task: {document_id}")
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(pipeline_engine.process_document(document_id, job_id))
    else:
        loop.run_until_complete(pipeline_engine.process_document(document_id, job_id))
    return {"status": "success", "document_id": document_id, "job_id": job_id}
