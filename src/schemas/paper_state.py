from pydantic import BaseModel
from typing import Dict, List, Any

from schemas.response_schema import PaperSummary


class PaperState(BaseModel):

    summary: PaperSummary

    sections: Dict[str, str]

    equations: List[dict]

    tables: List[dict]