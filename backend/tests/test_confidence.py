import pytest
from app.services.confidence_service import confidence_service
from app.models.extraction import ValidationResult
from app.models.document import DocumentType

@pytest.mark.asyncio
async def test_confidence_scoring():
    val_passed = [
        ValidationResult(rule_name="rule1", status="PASSED", message="ok"),
        ValidationResult(rule_name="rule2", status="PASSED", message="ok")
    ]
    ext_dict = {"a": "1", "b": "2", "c": "3"}
    
    score = await confidence_service.calculate_confidence(
        ocr_confidence=0.95,
        llm_confidence=0.92,
        validation_results=val_passed,
        extraction_dict=ext_dict,
        doc_type=DocumentType.INVOICE
    )
    
    assert score >= 0.90
