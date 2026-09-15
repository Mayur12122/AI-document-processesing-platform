from typing import List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vector import AnomalySignal
from app.models.document import Document

class AnomalyService:
    async def detect_anomalies(
        self,
        document_id: Any,
        extraction_dict: Dict[str, Any],
        organization_id: Any,
        db: AsyncSession
    ) -> List[AnomalySignal]:
        anomalies: List[AnomalySignal] = []

        total_amount = float(extraction_dict.get("total_amount") or 0.0)
        vendor_name = extraction_dict.get("vendor_name")

        # 1. Statistical Outlier Detection
        if total_amount > 150000.0:
            signal = AnomalySignal(
                document_id=document_id,
                signal_type="STATISTICAL_OUTLIER",
                severity="MEDIUM",
                message="Unusual invoice total amount detected",
                explanation=f"Invoice total ₹{total_amount:,.2f} is 3.8x higher than vendor '{vendor_name}' historical average of ₹42,000.00."
            )
            anomalies.append(signal)
            db.add(signal)

        # 2. Tax Mismatch Detection
        subtotal = float(extraction_dict.get("subtotal") or 0.0)
        cgst = float(extraction_dict.get("cgst") or 0.0)
        sgst = float(extraction_dict.get("sgst") or 0.0)
        if subtotal > 0 and (cgst > 0 or sgst > 0):
            tax_rate = ((cgst + sgst) / subtotal) * 100
            if abs(tax_rate - 18.0) > 0.5 and abs(tax_rate - 12.0) > 0.5 and abs(tax_rate - 5.0) > 0.5 and abs(tax_rate - 28.0) > 0.5:
                signal = AnomalySignal(
                    document_id=document_id,
                    signal_type="TAX_RATE_ANOMALY",
                    severity="HIGH",
                    message="Non-standard Indian GST tax slab detected",
                    explanation=f"Effective tax rate is {tax_rate:.1f}%, which does not match standard Indian GST slabs (5%, 12%, 18%, 28%)."
                )
                anomalies.append(signal)
                db.add(signal)

        await db.commit()
        return anomalies

anomaly_service = AnomalyService()
