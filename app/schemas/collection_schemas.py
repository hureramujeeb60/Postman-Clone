from pydantic import BaseModel

class RequestPayload(BaseModel):
    name: str

class UpdatePayload(BaseModel):
    new_name: str