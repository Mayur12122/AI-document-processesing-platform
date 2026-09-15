from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 18.0
    total: float = 0.0

class InvoiceExtraction(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Invoice or Bill reference number")
    invoice_date: Optional[str] = Field(None, description="Date of issue (YYYY-MM-DD)")
    vendor_name: Optional[str] = Field(None, description="Vendor or Seller legal business name")
    vendor_gstin: Optional[str] = Field(None, description="15-character Indian GSTIN of vendor")
    buyer_name: Optional[str] = Field(None, description="Buyer or Client legal business name")
    buyer_gstin: Optional[str] = Field(None, description="15-character Indian GSTIN of buyer")
    subtotal: Optional[float] = Field(None, description="Subtotal amount before tax")
    taxable_amount: Optional[float] = Field(None, description="Taxable base amount")
    cgst: Optional[float] = Field(0.0, description="Central GST amount")
    sgst: Optional[float] = Field(0.0, description="State GST amount")
    igst: Optional[float] = Field(0.0, description="Integrated GST amount")
    total_amount: Optional[float] = Field(None, description="Total invoice grand total")
    currency: str = Field("INR", description="Currency symbol/code")
    payment_due_date: Optional[str] = Field(None, description="Payment due date")
    line_items: List[InvoiceLineItem] = Field(default_factory=list)

class ContractExtraction(BaseModel):
    contract_number: Optional[str] = None
    parties: List[str] = Field(default_factory=list)
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    renewal_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    termination_clause: Optional[str] = None
    jurisdiction: Optional[str] = None

class BankTransaction(BaseModel):
    date: str
    description: str
    type: str  # DEBIT | CREDIT
    amount: float
    balance_after: float

class BankStatementExtraction(BaseModel):
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    statement_period: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    transactions: List[BankTransaction] = Field(default_factory=list)
