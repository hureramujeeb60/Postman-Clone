from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import requests, params, collections
import logging

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_or_404(db: AsyncSession, model, id, message="Resource not found"):
    result = await db.execute(select(model).where(model.c.id == id))
    result = result.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=message)
    return result

async def check_collection_exists(db: AsyncSession, collection_id: int):
    result = await db.execute(select(collections).where(collections.c.id == collection_id))
    collection = result.fetchone()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection

async def check_requests_exist(db: AsyncSession, collection_id: int):
    result = await db.execute(select(requests).where(requests.c.collection_id == collection_id))
    requests_list = result.fetchall()
    if not requests_list:
        raise HTTPException(status_code=404, detail="No requests found for this collection ID")
    return requests_list

async def check_request_exists(db: AsyncSession, request_id: int):
    result = await db.execute(select(requests).where(requests.c.id == request_id))
    request_exists = result.fetchone()
    if not request_exists:
        raise HTTPException(status_code=404, detail="Request not found")
    return request_exists

async def check_param_exists(db: AsyncSession, param_id: int):
    result = await db.execute(select(params).where(params.c.id == param_id))
    param_exists = result.fetchone()
    if not param_exists:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return param_exists

def handle_server_error(e):
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def validate_http_method(method: str):
    if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        raise HTTPException(status_code=400, detail="Unsupported HTTP method")

def validate_request_body(method: str, body):
    if method in ["POST", "PUT", "PATCH"] and not body:
        raise HTTPException(status_code=400, detail="Body is required for POST, PUT, and PATCH requests")
