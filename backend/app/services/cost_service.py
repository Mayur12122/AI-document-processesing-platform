from typing import Tuple, Dict, Any
from app.models.document import DocumentType

class CostService:
    # Token Pricing (USD per 1k tokens)
    RATES = {
        "local": {"input": 0.0, "output": 0.0},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105}
    }

    def route_model(self, doc_type: DocumentType, page_count: int, initial_confidence: float) -> str:
        """
        Dynamically routes processing:
        - Simple / standard docs -> Cheap / local model
        - Complex / multi-page / low confidence -> Premium model
        """
        if initial_confidence < 0.70 or page_count > 5:
            return "gpt-4o"
        elif doc_type in [DocumentType.CONTRACT, DocumentType.BANK_STATEMENT]:
            return "gemini-1.5-flash"
        else:
            return "local"

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rate = self.RATES.get(model, self.RATES["local"])
        input_cost = (input_tokens / 1000.0) * rate["input"]
        output_cost = (output_tokens / 1000.0) * rate["output"]
        usd_cost = input_cost + output_cost
        inr_cost = usd_cost * 83.5 # Convert USD to INR
        return round(inr_cost, 4)

cost_service = CostService()
