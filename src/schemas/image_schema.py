from pydantic import BaseModel
from typing import List, Optional


class FigureExplanation(BaseModel):
    page: int
    figure_index: int
    image_path: str
    explanation: str


class ImageAgentResponse(BaseModel):
    figures: List[FigureExplanation]
    gif_path: Optional[str] = None