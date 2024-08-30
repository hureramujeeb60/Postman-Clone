from fastapi import APIRouter, HTTPException, Depends
import logging
from sqlalchemy.orm import Session
import requests as req
from pydantic import BaseModel
from app.database import get_db
from app.models import collections, requests, params

router = APIRouter()

# Set up the logger
logging.basicConfig(level=logging.INFO)  # You can adjust the level as needed
logger = logging.getLogger(__name__)

@router.get("/send")
async def send_request():
    return {"message": "This is the send endpoint"}

class RequestPayload(BaseModel):
    url: str
    method: str
    collection_id: int
    body: str = None
    bodytype: str = None
    param_list: dict = None


@router.post("/send")
async def send_request(payload: RequestPayload, db: Session = Depends(get_db)):
    try:
        logger.info("Received request payload")
        logger.info(f"Payload: {payload}")

        new_request = requests.insert().values(
            url=payload.url,
            method=payload.method,
            body=payload.body,
            bodytype=payload.bodytype,
            collection_id = payload.collection_id
        )
        
        logger.info("Inserting new request")
        result = db.execute(new_request)
        logger.info(f"Insert result: {result}")

        db.commit()
        logger.info("Request committed to database")

        if payload.param_list:
            logger.info("Inserting params")
            for key, value in payload.param_list.items():
                new_param = params.insert().values(
                    key=key,
                    value=value,
                    request_id=result.inserted_primary_key[0]
                )
                db.execute(new_param)
            db.commit()
            logger.info("Params committed to database")

        response = req.request(payload.method, payload.url, data=payload.body, params=payload.param_list)
        logger.info(f"Request made to external API. Status: {response.status_code}")
        
        return {"status_code": response.status_code, "content": response.content}

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


# @router.post("/send")
# async def send_request(payload: RequestPayload, db: Session = Depends(get_db)):
#     # Store request in the database
#     new_request = requests.insert().values(
#         url=payload.url,
#         method=payload.method,
#         body=payload.body,
#         bodytype=payload.bodytype,
#     )
#     result = db.execute(new_request)
#     db.commit()

#     request_id = result.inserted_primary_key[0]
#     if not request_id:
#         raise HTTPException(status_code=500, detail="Failed to retrieve request ID")

#     # If params are passed, store them in the database
#     if payload.param_list:
#         for key, value in payload.param_list.items():
#             new_param = params.insert().values(
#                 key=key,
#                 value=value,
#                 request_id=request_id
#             )
#             db.execute(new_param)
#             print(f"Inserted param: {key}={value} for request_id={request_id}")
#         db.commit()

#     # Make the actual request
#     try:
#         response = req.request(payload.method, payload.url, data=payload.body, params=payload.param_list)
#         return {"status_code": response.status_code, "content": response.content}
#     except req.RequestException as e:
#         raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
