from pydantic import BaseModel, Field
from typing import Optional, Dict

class RequestBody(BaseModel):
    collection_id: Optional[int] = Field(None, description="ID of the collection")
    url: str = Field(..., description="URL for the request")
    method: str = Field(..., description="HTTP method to use (GET, POST, etc.)")
    body: Optional[Dict] = Field(None, description="Request body for POST, PUT, or PATCH methods")
    params: Optional[Dict] = Field(None, description="Query parameters for GET or DELETE methods")
    bodytype: str = Field(..., description="Type of request body ('raw', 'form')")