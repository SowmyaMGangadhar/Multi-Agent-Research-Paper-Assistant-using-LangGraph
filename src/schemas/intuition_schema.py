from pydantic import BaseModel


class IntuitionResponse(BaseModel):

    intuition: str