from pydantic import BaseModel


class FinalResponse(BaseModel):
    answer: str