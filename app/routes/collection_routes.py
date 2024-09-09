from fastapi import APIRouter, HTTPException, Depends, Path
import logging
from typing import List
from sqlalchemy import update
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import collections, requests, params, response

router = APIRouter()

# Set up the logger
logging.basicConfig(level=logging.INFO)  # You can adjust the level as needed
logger = logging.getLogger(__name__)

class RequestPayload(BaseModel):
    name: str

@router.post("/add_collection")
async def add_collection(payload: RequestPayload, db: Session = Depends(get_db)):
    try:
        # Insert the new collection
        query = collections.insert().values(name=payload.name)
        result = db.execute(query)
        db.commit()

        # Get the inserted collection ID
        inserted_id = result.inserted_primary_key[0]

        return {"message": "Collection added successfully", "collection_id": inserted_id}
    
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


def serialize_collection(collection):
    return {
        "id": collection.id,
        "name": collection.name,
        # Include other fields as necessary
    }

@router.get("/collections")
async def get_all_collections(db: Session = Depends(get_db)):
    collections_list = db.query(collections).all()
    if not collections_list:
        raise HTTPException(status_code=404, detail="No collections found")
    collections_data = [serialize_collection(c) for c in collections_list]
    return collections_data


def serialize_requests(requests):
    return {
        "id": requests.id,
        "url": requests.url,
        "method": requests.method,
        "body": requests.body,
        "bodytype": requests.bodytype,
        "collection_id": requests.collection_id
        # Include other fields as necessary
    }

@router.get("/collections/{collection_id}/requests")
async def get_requests_by_collection_id(collection_id: int, db: Session = Depends(get_db)):
    requests_list = db.query(requests).filter(requests.c.collection_id == collection_id).all()
    if not requests_list:
        raise HTTPException(status_code=404, detail="No requests found for this collection ID")
    request_data = [serialize_requests(c) for c in requests_list]
    return request_data


@router.get("/collections/{collection_id}")
async def get_collection_by_id(collection_id: int, db: Session = Depends(get_db)):
    collection = db.query(collections).filter_by(id=collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"collection_id": collection.id, "name": collection.name, "status_code": 200}



@router.delete("/delete_collection/{collection_id}")
async def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    # Verify if the collection exists
    collection = db.execute(select(collections).filter_by(id=collection_id)).fetchone()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    try:
        # Retrieve the IDs of all requests associated with the collection
        request_ids = db.execute(select(requests.c.id).where(requests.c.collection_id == collection_id)).scalars().all()
        
        if request_ids:
            # Delete associated responses
            db.execute(delete(response).where(response.c.request_id.in_(request_ids)))
            # Delete associated params
            db.execute(delete(params).where(params.c.request_id.in_(request_ids)))
            # Delete associated requests
            db.execute(delete(requests).where(requests.c.collection_id == collection_id))

        # Finally, delete the collection itself
        db.execute(delete(collections).where(collections.c.id == collection_id))

        db.commit()
        return {"message": "Collection and all associated data (requests, responses, params) deleted successfully"}
    except Exception as e:
        logger.error(f"Error occurred during deletion: {e}")
        db.rollback()  # Rollback the transaction in case of error
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")



class UpdatePayload(BaseModel):
    new_name: str

@router.patch("/update_collection/{collection_id}")
async def update_collection(
    collection_id: int, 
    payload: UpdatePayload, 
    db: Session = Depends(get_db)
):
    try:
        # Update the collection name where collection ID matches
        stmt = update(collections).where(collections.c.id == collection_id).values(name=payload.new_name)
        
        # Execute the update statement
        result = db.execute(stmt)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        db.commit()  # Commit the transaction
        return {"message": "Collection updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating collection: {str(e)}")


