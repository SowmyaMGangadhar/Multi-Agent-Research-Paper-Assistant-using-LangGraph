from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatState(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    current_paper_query: Optional[str] = None