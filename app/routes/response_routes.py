from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from app.database import get_db
from app.models import response, requests
from app.utils.utils import get_or_404, handle_server_error
from app.schemas.response_schema import SaveResponseRequest, UpdateResponseRequest

router = APIRouter()

@router.post("/responses")
async def save_response(data: SaveResponseRequest, db: AsyncSession = Depends(get_db)):
    try:
        await get_or_404(db, requests, data.request_id, "Request not found")

        new_response = response.insert().values(
            request_id=data.request_id,
            body=data.body,  
            status_code=data.status_code
        )
        await db.execute(new_response)
        await db.commit()
        
        return {"message": "Response saved successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)

@router.get("/responses/{response_id}")
async def get_response(response_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await get_or_404(db, response, response_id, "Response not found")

        response_data = {
            "response_id": result.id,
            "request_id": result.request_id,
            "body": result.body,
            "status_code": result.status_code
        }
        return response_data
    except Exception as e:
        handle_server_error(e)

@router.put("/responses/{response_id}")
async def update_response(response_id: int, data: UpdateResponseRequest, db: AsyncSession = Depends(get_db)):
    try:
        update_values = {}
        if data.body is not None:
            update_values['body'] = data.body
        if data.status_code is not None:
            update_values['status_code'] = data.status_code

        if not update_values:
            raise HTTPException(status_code=400, detail="No values provided for update")

        await get_or_404(db, response, response_id, "Response not found")

        query = update(response).where(response.c.id == response_id).values(update_values)
        await db.execute(query)
        await db.commit()

        return {"message": "Response updated successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)

@router.delete("/responses/{response_id}")
async def delete_response(response_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await get_or_404(db, response, response_id, "Response not found")

        query = response.delete().where(response.c.id == response_id)
        await db.execute(query)
        await db.commit()

        return {"message": "Response deleted successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)
