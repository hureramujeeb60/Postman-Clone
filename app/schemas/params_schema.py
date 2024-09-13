from pydantic import BaseModel

class AddParamPayload(BaseModel):
    key: str
    value: str
    request_id: int

class UpdateParamPayload(BaseModel):
    key: str = None
    value: str = None