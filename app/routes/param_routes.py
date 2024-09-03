from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import params
from sqlalchemy import update

router = APIRouter()

class AddParamPayload(BaseModel):
    key: str
    value: str
    request_id: int

@router.post("/add_param")
async def add_param(payload: AddParamPayload, db: Session = Depends(get_db)):
    try:
        new_param = params.insert().values(
            key=payload.key,
            value=payload.value,
            request_id=payload.request_id
        )
        db.execute(new_param)
        db.commit()
        return {"message": "Parameter added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add parameter: {str(e)}")

class UpdateParamPayload(BaseModel):
    key: str = None
    value: str = None

@router.put("/update_param/{param_id}")
async def update_param(param_id: int, payload: UpdateParamPayload, db: Session = Depends(get_db)):
    update_values = {}
    
    if payload.key is not None:
        update_values['key'] = payload.key
    if payload.value is not None:
        update_values['value'] = payload.value
    
    if not update_values:
        raise HTTPException(status_code=400, detail="No values provided for update")

    query = update(params).where(params.c.id == param_id).values(update_values)
    result = db.execute(query)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Parameter not found")
    
    db.commit()
    return {"message": "Parameter updated successfully"}

class DeleteParamPayload(BaseModel):
    id: int

@router.delete("/delete_param")
async def delete_param(payload: DeleteParamPayload, db: Session = Depends(get_db)):
    param = db.query(params).filter_by(id=payload.id).first()
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")
    
    try:
        db.delete(param)
        db.commit()
        return {"message": "Parameter deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete parameter: {str(e)}")