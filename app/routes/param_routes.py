from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models import params
from sqlalchemy import update, delete, select
from app.utils.utils import check_request_exists, check_param_exists, handle_server_error, logger
from app.schemas.params_schema import AddParamPayload, UpdateParamPayload

router = APIRouter()

@router.post("/add_param")
async def add_param(payload: AddParamPayload, db: AsyncSession = Depends(get_db)):
    try:
        await check_request_exists(db, payload.request_id)

        new_param = params.insert().values(
            key=payload.key,
            value=payload.value,
            request_id=payload.request_id
        )
        await db.execute(new_param)
        await db.commit()

        logger.info(f"Parameter added successfully to request {payload.request_id}")
        return {"message": "Parameter added successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)

@router.put("/update_param/{param_id}")
async def update_param(param_id: int, payload: UpdateParamPayload, db: AsyncSession = Depends(get_db)):
    try:
        await check_param_exists(db, param_id)

        update_values = {}
        if payload.key is not None:
            update_values['key'] = payload.key
        if payload.value is not None:
            update_values['value'] = payload.value

        if not update_values:
            raise HTTPException(status_code=400, detail="No values provided for update")

        query = update(params).where(params.c.id == param_id).values(update_values)
        await db.execute(query)
        await db.commit()

        logger.info(f"Parameter with ID {param_id} updated successfully")
        return {"message": "Parameter updated successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)

@router.delete("/delete_param/{param_id}")
async def delete_param(param_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await check_param_exists(db, param_id)

        query = delete(params).where(params.c.id == param_id)
        await db.execute(query)
        await db.commit()

        logger.info(f"Parameter with ID {param_id} deleted successfully")
        return {"message": "Parameter deleted successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)


@router.get("/get_params/{request_id}")
async def get_params(request_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await check_request_exists(db, request_id)

        query = select(params).where(params.c.request_id == request_id)
        result = await db.execute(query)
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No parameters found for the given request_id")

        params_list = [{"id": row.id, "key": row.key, "value": row.value} for row in rows]

        logger.info(f"Retrieved parameters for request {request_id}")
        return {"request_id": request_id, "params": params_list}
    except Exception as e:
        handle_server_error(e)

