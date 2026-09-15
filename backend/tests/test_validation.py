import pytest
from app.services.validation_service import validation_service
from app.models.document import DocumentType

@pytest.mark.asyncio
async def test_valid_invoice_arithmetic():
    extraction_dict = {
        "subtotal": 100000.0,
        "cgst": 9000.0,
        "sgst": 9000.0,
        "igst": 0.0,
        "total_amount": 118000.0,
        "vendor_gstin": "27AABCU9603R1ZN",
        "invoice_number": "INV-2026-9014",
        "invoice_date": "2026-09-15",
        "vendor_name": "ABC Tech"
    }
    
    # Mock DB session for testing rules logic
    class MockDB:
        def add(self, item): pass
        async def commit(self): pass

    results = await validation_service.validate_extraction("ext-1", extraction_dict, DocumentType.INVOICE, MockDB())
    
    arithmetic_res = next(r for r in results if r.rule_name == "invoice_arithmetic_check")
    assert arithmetic_res.status == "PASSED"

    gstin_res = next(r for r in results if r.rule_name == "vendor_gstin_check")
    assert gstin_res.status == "PASSED"

@pytest.mark.asyncio
async def test_invalid_invoice_arithmetic_mismatch():
    extraction_dict = {
        "subtotal": 100000.0,
        "cgst": 9000.0,
        "sgst": 9000.0,
        "total_amount": 150000.0, # Intentional Mismatch
        "vendor_gstin": "INVALID_GST",
        "invoice_number": "INV-2026-9099"
    }
    
    class MockDB:
        def add(self, item): pass
        async def commit(self): pass

    results = await validation_service.validate_extraction("ext-2", extraction_dict, DocumentType.INVOICE, MockDB())
    
    arithmetic_res = next(r for r in results if r.rule_name == "invoice_arithmetic_check")
    assert arithmetic_res.status == "FAILED"

    gstin_res = next(r for r in results if r.rule_name == "vendor_gstin_check")
    assert gstin_res.status == "WARNING"
