from pydantic import BaseModel
from typing import List


class PaperSummary(BaseModel):

    title: str

    abstract: str   

    summary: str