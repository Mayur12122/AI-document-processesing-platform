from typing import List, Dict, Any
from app.models.extraction import ValidationResult
from app.models.document import DocumentType

class ConfidenceService:
    async def calculate_confidence(
        self,
        ocr_confidence: float,
        llm_confidence: float,
        validation_results: List[ValidationResult],
        extraction_dict: Dict[str, Any],
        doc_type: DocumentType
    ) -> float:
        # 1. OCR Score (Weight: 25%)
        w_ocr = 0.25 * max(0.0, min(1.0, ocr_confidence))

        # 2. LLM Extraction Score (Weight: 25%)
        w_llm = 0.25 * max(0.0, min(1.0, llm_confidence))

        # 3. Validation Results Score (Weight: 20%)
        if not validation_results:
            w_val = 0.20
        else:
            passed = sum(1 for v in validation_results if v.status == "PASSED")
            w_val = 0.20 * (passed / len(validation_results))

        # 4. Schema Validity Score (Weight: 20%)
        w_schema = 0.20

        # 5. Field Completeness Score (Weight: 10%)
        non_null_fields = sum(1 for v in extraction_dict.values() if v is not None and v != "")
        total_fields = max(len(extraction_dict), 1)
        w_completeness = 0.10 * (non_null_fields / total_fields)

        final_score = w_ocr + w_llm + w_val + w_schema + w_completeness
        return round(max(0.0, min(1.0, final_score)), 2)

confidence_service = ConfidenceService()
