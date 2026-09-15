from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Dict
import re
from app.models.document import DocumentType

class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float
    signals: List[str]

class DocumentClassifier(ABC):
    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        pass

class RuleAndLLMClassifier(DocumentClassifier):
    async def classify(self, text: str) -> ClassificationResult:
        text_upper = text.upper()
        signals = []

        # Invoice / GST Document signals
        invoice_keywords = ["TAX INVOICE", "INVOICE NO", "INVOICE NUMBER", "BILL TO", "TAXABLE AMOUNT", "CGST", "SGST", "IGST", "GSTIN"]
        invoice_matches = [kw for kw in invoice_keywords if kw in text_upper]

        # Contract signals
        contract_keywords = ["AGREEMENT", "CONTRACT", "WHEREAS", "PARTY OF THE FIRST PART", "TERMS AND CONDITIONS", "JURISDICTION", "TERMINATION CLAUSE"]
        contract_matches = [kw for kw in contract_keywords if kw in text_upper]

        # Bank Statement signals
        bank_keywords = ["BANK STATEMENT", "ACCOUNT NUMBER", "OPENING BALANCE", "CLOSING BALANCE", "TRANSACTION DETAILS", "DEBIT", "CREDIT", "IFSC"]
        bank_matches = [kw for kw in bank_keywords if kw in text_upper]

        # Purchase Order signals
        po_keywords = ["PURCHASE ORDER", "P.O. NUMBER", "PO NO", "VENDOR CODE", "DELIVERY DATE"]
        po_matches = [kw for kw in po_keywords if kw in text_upper]

        if len(invoice_matches) >= 2:
            if "GSTIN" in invoice_matches and ("CGST" in invoice_matches or "IGST" in invoice_matches):
                return ClassificationResult(
                    document_type=DocumentType.INVOICE,
                    confidence=0.96,
                    signals=[f"Matched keywords: {', '.join(invoice_matches)}"]
                )
            return ClassificationResult(
                document_type=DocumentType.INVOICE,
                confidence=0.88,
                signals=[f"Matched keywords: {', '.join(invoice_matches)}"]
            )

        if len(contract_matches) >= 2:
            return ClassificationResult(
                document_type=DocumentType.CONTRACT,
                confidence=0.94,
                signals=[f"Matched contract terms: {', '.join(contract_matches)}"]
            )

        if len(bank_matches) >= 2:
            return ClassificationResult(
                document_type=DocumentType.BANK_STATEMENT,
                confidence=0.95,
                signals=[f"Matched bank statement terms: {', '.join(bank_matches)}"]
            )

        if len(po_matches) >= 2:
            return ClassificationResult(
                document_type=DocumentType.PURCHASE_ORDER,
                confidence=0.90,
                signals=[f"Matched PO terms: {', '.join(po_matches)}"]
            )

        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.40,
            signals=["No strong document classification keywords detected"]
        )
