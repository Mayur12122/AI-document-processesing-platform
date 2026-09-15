import re
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentType
from app.models.extraction import ValidationResult

class ValidationService:
    # 15-character Indian GSTIN Regex
    GSTIN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'

    async def validate_extraction(
        self, 
        extraction_id: Any, 
        extraction_dict: Dict[str, Any], 
        doc_type: DocumentType,
        db: AsyncSession
    ) -> List[ValidationResult]:
        results: List[ValidationResult] = []

        if doc_type in [DocumentType.INVOICE, DocumentType.GST_DOCUMENT]:
            # Rule 1: Invoice Arithmetic Check
            subtotal = float(extraction_dict.get("subtotal") or 0.0)
            cgst = float(extraction_dict.get("cgst") or 0.0)
            sgst = float(extraction_dict.get("sgst") or 0.0)
            igst = float(extraction_dict.get("igst") or 0.0)
            total = float(extraction_dict.get("total_amount") or 0.0)

            expected_total = subtotal + cgst + sgst + igst
            if total > 0 and abs(expected_total - total) <= 2.0:
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="invoice_arithmetic_check",
                    field_name="total_amount",
                    status="PASSED",
                    message=f"Invoice totals are consistent: Subtotal ({subtotal}) + Taxes ({cgst + sgst + igst}) = Total ({total})"
                ))
            else:
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="invoice_arithmetic_check",
                    field_name="total_amount",
                    status="FAILED",
                    message=f"GST Mismatch: Calculated expected total ({expected_total:.2f}) does not match invoice total ({total:.2f})"
                ))

            # Rule 2: Vendor GSTIN Validation
            vendor_gstin = extraction_dict.get("vendor_gstin")
            if vendor_gstin and re.match(self.GSTIN_REGEX, str(vendor_gstin)):
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="vendor_gstin_check",
                    field_name="vendor_gstin",
                    status="PASSED",
                    message="Valid 15-character Indian GSTIN format"
                ))
            else:
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="vendor_gstin_check",
                    field_name="vendor_gstin",
                    status="WARNING",
                    message=f"Invalid or missing vendor GSTIN: '{vendor_gstin}'"
                ))

            # Rule 3: Required Fields Check
            required_fields = ["invoice_number", "invoice_date", "vendor_name", "total_amount"]
            missing = [f for f in required_fields if not extraction_dict.get(f)]
            if not missing:
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="required_fields_check",
                    field_name="all",
                    status="PASSED",
                    message="All mandatory invoice metadata fields are present"
                ))
            else:
                results.append(ValidationResult(
                    extraction_id=extraction_id,
                    rule_name="required_fields_check",
                    field_name="missing",
                    status="FAILED",
                    message=f"Missing required fields: {', '.join(missing)}"
                ))

        for res in results:
            db.add(res)
        await db.commit()
        return results

validation_service = ValidationService()
