from fastapi import APIRouter, HTTPException, Depends, Path
from app.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import update
from app.models import response
from app.database import database

router = APIRouter()

class SaveResponseRequest(BaseModel):
    request_id: int
    body: dict  # Change from str to dict for JSON
    status_code: int


@router.post("/responses")
async def save_response(data: SaveResponseRequest, db: Session = Depends(get_db)):
    try:
        # Save the response body as a JSONB object
        new_response = response.insert().values(
            request_id=data.request_id,
            body=data.body,  # Will now be stored as JSON
            status_code=data.status_code
        )
        db.execute(new_response)
        db.commit()
        return {"message": "Response saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save response: {str(e)}")
    

class UpdateResponseRequest(BaseModel):
    body: dict = None  # Change from str to dict for JSON
    status_code: int = None


@router.put("/responses/{response_id}")
async def update_response(response_id: int, data: UpdateResponseRequest, db=Depends(get_db)):
    update_values = {}
    
    if data.body is not None:
        update_values['body'] = data.body  # Store the body as JSON
    if data.status_code is not None:
        update_values['status_code'] = data.status_code
    
    if not update_values:
        raise HTTPException(status_code=400, detail="No values provided for update")

    query = update(response).where(response.c.id == response_id).values(update_values)
    result = db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Response not found")
    
    db.commit()  # Commit the transaction

    return {"message": "Response updated successfully"}


@router.delete("/responses/{response_id}")
async def delete_response(response_id: int, db: Session = Depends(get_db)):
    # Check if the response exists before deleting
    query = response.delete().where(response.c.id == response_id)
    result = db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Response not found")
    
    db.commit()  # Commit the transaction
    
    return {"message": "Response deleted successfully"}
