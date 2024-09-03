from fastapi import APIRouter, HTTPException, Depends
import logging
from typing import List
from sqlalchemy import update
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import collections, requests

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


@router.get("/collections/{collection_id}")
async def get_collection_by_id(collection_id: int, db: Session = Depends(get_db)):
    collection = db.query(collections).filter_by(id=collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"collection_id": collection.id, "name": collection.name, "status_code": 200}


class DeletePayload(BaseModel):
    id: int


@router.delete("/delete_collection")
async def delete_collection(payload: DeletePayload, db: Session = Depends(get_db)):
    # Use SQLAlchemy `select` statement to verify if the collection exists
    collection = db.execute(select(collections).filter_by(id=payload.id)).fetchone()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    try:
        # Delete associated requests first
        db.execute(delete(requests).where(requests.c.collection_id == payload.id))
        
        # Then delete the collection itself
        db.execute(delete(collections).where(collections.c.id == payload.id))
        
        db.commit()
        return {"message": "Collection and associated requests deleted successfully"}
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        db.rollback()  # Rollback the transaction in case of error
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


class UpdatePayload(BaseModel):
    id: int
    new_name: str

@router.patch("/update_collection")
async def update_collection(payload: UpdatePayload, db=Depends(get_db)):

    stmt = update(collections).where(collections.c.id == payload.id).values(name=payload.new_name)
    
    result = db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    db.commit()  # Commit the transaction
    return {"message": "Collection updated successfully"}