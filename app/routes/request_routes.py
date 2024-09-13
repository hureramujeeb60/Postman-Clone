from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, delete
from app.database import get_db
from app.models import collections, requests, params, response, BodyType
from app.utils.utils import get_or_404, handle_server_error, validate_http_method, validate_request_body, logger
from app.schemas.request_schema import RequestBody

router = APIRouter()

@router.delete("/requests/{request_id}")
async def delete_request(request_id: int = Path(..., description="ID of the request to delete"), db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Deleting request with ID {request_id}")

        await db.execute(delete(response).where(response.c.request_id == request_id))
        await db.execute(delete(params).where(params.c.request_id == request_id))

        delete_result = await db.execute(delete(requests).where(requests.c.id == request_id))

        if delete_result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found")

        await db.commit()
        return {"detail": "Request and associated data deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        handle_server_error(e)


@router.post("/save_request")
async def save_request(data: RequestBody, db: AsyncSession = Depends(get_db)):
    try:
        if data.collection_id is not None:
            await get_or_404(db, collections, data.collection_id, "Collection not found")

        validate_http_method(data.method)

        validate_request_body(data.method, data.body)

        query = insert(requests).values(
            url=data.url,
            method=data.method,
            body=data.body if data.method in ["POST", "PUT", "PATCH"] else None,
            bodytype=BodyType[data.bodytype] if data.bodytype else None,
            collection_id=data.collection_id
        ).returning(requests.c.id)

        result = await db.execute(query)
        request_id = result.scalar()  # Updated this to extract the scalar value directly

        await db.commit()

        response_data = {
            "status": "success",
            "id": request_id,
            "method": data.method,
            "url": data.url,
            "collection_id": data.collection_id,
            "body_type": data.bodytype,
        }

        if data.method in ["POST", "PATCH", "PUT"]:
            response_data["body"] = data.body

        logger.info(f"Inserted request with ID: {request_id}")
        return response_data
    except Exception as e:
        await db.rollback()
        handle_server_error(e)
