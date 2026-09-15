import time
import json
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.document import Document, DocumentPage, DocumentStatus, DocumentType
from app.models.job import ProcessingJob, ProcessingStep
from app.models.extraction import Extraction, ExtractedField
from app.models.review import ReviewTask
from app.services.storage_service import storage_service
from app.providers.ocr_provider import TesseractOCRProvider, FallbackOCRProvider
from app.providers.classifier_provider import RuleAndLLMClassifier
from app.providers.llm_provider import LocalDeterministicLLMProvider
from app.core.config import settings

class PipelineEngine:
    async def process_document(self, document_id: str, job_id: str):
        async with AsyncSessionLocal() as db:
            doc_uuid = uuid.UUID(document_id)
            job_uuid = uuid.UUID(job_id)

            doc_res = await db.execute(select(Document).where(Document.id == doc_uuid))
            document = doc_res.scalars().first()
            
            job_res = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_uuid))
            job = job_res.scalars().first()

            if not document or not job:
                logger.error(f"Pipeline error: Document {document_id} or Job {job_id} not found")
                return

            try:
                # Stage 1: INGESTION
                await self._update_job_stage(db, job, "INGESTION", "PROCESSING")
                document.status = DocumentStatus.PROCESSING
                await db.commit()

                file_bytes = await storage_service.get_document_bytes(document.storage_path)

                # Stage 2: OCR
                await self._update_job_stage(db, job, "OCR", "PROCESSING")
                ocr_provider = TesseractOCRProvider() if settings.DEFAULT_OCR_PROVIDER == "tesseract" else FallbackOCRProvider()
                ocr_result = await ocr_provider.extract_text(file_bytes, document.mime_type)

                # Save OCR pages & blocks
                for page_res in ocr_result.pages:
                    doc_page = DocumentPage(
                        document_id=document.id,
                        page_number=page_res.page_number,
                        width=page_res.width,
                        height=page_res.height,
                        ocr_text=page_res.text,
                        ocr_blocks_json=[b.model_dump() for b in page_res.blocks]
                    )
                    db.add(doc_page)

                document.status = DocumentStatus.OCR_COMPLETED
                await db.commit()

                # Stage 3: CLASSIFICATION
                await self._update_job_stage(db, job, "CLASSIFICATION", "PROCESSING")
                classifier = RuleAndLLMClassifier()
                class_res = await classifier.classify(ocr_result.full_text)
                
                document.document_type = class_res.document_type
                document.status = DocumentStatus.CLASSIFIED
                await db.commit()

                # Stage 4: EXTRACTION
                await self._update_job_stage(db, job, "EXTRACTION", "PROCESSING")
                document.status = DocumentStatus.EXTRACTING
                await db.commit()

                llm_provider = LocalDeterministicLLMProvider()
                ext_dict, llm_conf, in_tok, out_tok = await llm_provider.extract_structured_data(
                    ocr_result.full_text, 
                    document.document_type
                )

                job.input_tokens = in_tok
                job.output_tokens = out_tok
                job.cost_estimate = round((in_tok * 0.0000015) + (out_tok * 0.000002), 6)

                extraction = Extraction(
                    document_id=document.id,
                    job_id=job.id,
                    document_type=document.document_type.value,
                    extraction_json=ext_dict,
                    confidence_overall=llm_conf
                )
                db.add(extraction)
                await db.commit()
                await db.refresh(extraction)

                # Save Extracted Fields with sample bounding box coordinates for Document Viewer
                for key, val in ext_dict.items():
                    if key != "line_items":
                        field = ExtractedField(
                            extraction_id=extraction.id,
                            field_name=key,
                            field_value=str(val) if val is not None else "",
                            confidence=llm_conf,
                            page_number=1,
                            bounding_box_json=[100, 150, 400, 40]
                        )
                        db.add(field)

                await db.commit()

                # Stage 5 & 6: VALIDATION & CONFIDENCE SCORING
                await self._update_job_stage(db, job, "VALIDATION", "PROCESSING")
                from app.services.validation_service import validation_service
                from app.services.confidence_service import confidence_service
                
                val_results = await validation_service.validate_extraction(extraction.id, ext_dict, document.document_type, db)
                final_confidence = await confidence_service.calculate_confidence(
                    ocr_confidence=ocr_result.avg_confidence,
                    llm_confidence=llm_conf,
                    validation_results=val_results,
                    extraction_dict=ext_dict,
                    doc_type=document.document_type
                )

                document.confidence_score = final_confidence

                # Stage 7: REVIEW ROUTING
                if final_confidence < settings.AUTO_APPROVE_THRESHOLD:
                    document.status = DocumentStatus.REVIEW_REQUIRED
                    review_task = ReviewTask(
                        document_id=document.id,
                        organization_id=document.organization_id,
                        status="PENDING",
                        priority="HIGH" if final_confidence < settings.HUMAN_REVIEW_THRESHOLD else "MEDIUM"
                    )
                    db.add(review_task)
                else:
                    document.status = DocumentStatus.COMPLETED

                job.status = "COMPLETED"
                job.current_stage = "COMPLETED"
                await db.commit()
                logger.info(f"Pipeline completed for document {document_id} with status {document.status.value}")

            except Exception as e:
                logger.error(f"Pipeline failed for document {document_id}: {str(e)}", exc_info=True)
                document.status = DocumentStatus.FAILED
                job.status = "FAILED"
                job.error_message = str(e)
                await db.commit()

    async def _update_job_stage(self, db: AsyncSession, job: ProcessingJob, stage: str, status: str):
        job.current_stage = stage
        step = ProcessingStep(
            job_id=job.id,
            stage=stage,
            status=status,
            duration_ms=100.0
        )
        db.add(step)
        await db.commit()

pipeline_engine = PipelineEngine()
