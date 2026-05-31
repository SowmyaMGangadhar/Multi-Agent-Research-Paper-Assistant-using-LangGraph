from pydantic import BaseModel
from typing import List


class EquationExplanation(BaseModel):
    equation: str
    variables: str
    explanation: str
    intuition: str = "No separate intuition provided."


class MathResponse(BaseModel):
    equations: List[EquationExplanation]