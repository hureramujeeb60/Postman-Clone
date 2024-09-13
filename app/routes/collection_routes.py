from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import collections, requests, params, response
from sqlalchemy import update, delete, select
from app.utils.utils import check_collection_exists, check_requests_exist, handle_server_error, logger
from app.schemas.collection_schemas import RequestPayload, UpdatePayload

router = APIRouter()


@router.post("/add_collection")
async def add_collection(payload: RequestPayload, db: Session = Depends(get_db)):
    try:
        query = collections.insert().values(name=payload.name)
        result = await db.execute(query)
        await db.commit()

        inserted_id = result.inserted_primary_key[0]
        logger.info(f"Collection added with ID: {inserted_id}")

        return {"message": "Collection added successfully", "collection_id": inserted_id}
    except Exception as e:
        handle_server_error(e)


def serialize_collection(collection):
    return {
        "id": collection.id,
        "name": collection.name,
    }

@router.get("/collections")
async def get_all_collections(db: Session = Depends(get_db)):
    try:
        collections_list = await db.execute(select(collections))
        collections_data = [serialize_collection(c) for c in collections_list.scalars().all()]

        if not collections_data:
            raise HTTPException(status_code=404, detail="No collections found")

        logger.info("Retrieved all collections")
        return collections_data
    except Exception as e:
        handle_server_error(e)


def serialize_requests(requests):
    return {
        "id": requests.id,
        "url": requests.url,
        "method": requests.method,
        "body": requests.body,
        "bodytype": requests.bodytype,
        "collection_id": requests.collection_id
    }

@router.get("/collections/{collection_id}/requests")
async def get_requests_by_collection_id(collection_id: int, db: Session = Depends(get_db)):
    try:
        requests_list = await check_requests_exist(db, collection_id)
        request_data = [serialize_requests(c) for c in requests_list]

        logger.info(f"Retrieved requests for collection ID {collection_id}")
        return request_data
    except Exception as e:
        handle_server_error(e)


@router.get("/collections/{collection_id}")
async def get_collection_by_id(collection_id: int, db: Session = Depends(get_db)):
    try:
        collection = await check_collection_exists(db, collection_id)
        logger.info(f"Retrieved collection with ID {collection_id}")
        return {"collection_id": collection.id, "name": collection.name, "status_code": 200}
    except Exception as e:
        handle_server_error(e)

@router.delete("/delete_collection/{collection_id}")
async def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    try:
        await check_collection_exists(db, collection_id)

        request_ids = await db.execute(select(requests.c.id).where(requests.c.collection_id == collection_id))
        request_ids = request_ids.scalars().all()

        if request_ids:
            await db.execute(delete(response).where(response.c.request_id.in_(request_ids)))
            await db.execute(delete(params).where(params.c.request_id.in_(request_ids)))
            await db.execute(delete(requests).where(requests.c.collection_id == collection_id))

        await db.execute(delete(collections).where(collections.c.id == collection_id))
        await db.commit()

        logger.info(f"Collection and associated data deleted successfully for collection ID {collection_id}")
        return {"message": "Collection and all associated data deleted successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)
        

@router.patch("/update_collection/{collection_id}")
async def update_collection(collection_id: int, payload: UpdatePayload, db: Session = Depends(get_db)):
    try:
        stmt = update(collections).where(collections.c.id == collection_id).values(name=payload.new_name)

        result = await db.execute(stmt)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Collection not found")

        await db.commit()
        logger.info(f"Collection ID {collection_id} updated successfully")
        return {"message": "Collection updated successfully"}
    except Exception as e:
        await db.rollback()
        handle_server_error(e)
