from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import params
from sqlalchemy import update, delete, select  

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


@router.delete("/delete_param/{param_id}")
async def delete_param(param_id: int, db: Session = Depends(get_db)):
    # Use SQLAlchemy `select` to check if the param exists
    param = db.execute(select(params).where(params.c.id == param_id)).fetchone()
    
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")
    
    try:
        # Delete the param using the `delete` statement
        db.execute(delete(params).where(params.c.id == param_id))
        db.commit()
        return {"message": "Parameter deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete parameter: {str(e)}")


@router.get("/get_params/{request_id}")
async def get_params(request_id: int, db: Session = Depends(get_db)):
    try:
        # Query to get all parameters for the given request_id
        query = select(params).where(params.c.request_id == request_id)
        result = db.execute(query).fetchall()
        
        if not result:
            raise HTTPException(status_code=404, detail="No parameters found for the given request_id")
        
        # Format the result as a list of dictionaries
        params_list = [{"id": row.id, "key": row.key, "value": row.value} for row in result]
        
        return {"request_id": request_id, "params": params_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve parameters: {str(e)}")