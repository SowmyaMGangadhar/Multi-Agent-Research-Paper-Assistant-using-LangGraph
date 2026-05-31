from pydantic import BaseModel
from typing import List


class ComparisonResult(BaseModel):

    compared_papers: List[str]

    comparison: str

    key_differences: List[str]

    strengths: List[str]

    weaknesses: List[str]

    recommendation: str