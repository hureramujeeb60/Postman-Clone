from pydantic import BaseModel

class SaveResponseRequest(BaseModel):
    request_id: int
    body: dict  
    status_code: int = None

class UpdateResponseRequest(BaseModel):
    body: dict = None  
    status_code: int = None