from fastapi import APIRouter, HTTPException, Depends, Form, Request, Path
import logging
from typing import Optional, Dict
import httpx  # We'll use this for making HTTP requests
from sqlalchemy.orm import Session
import requests as req
from pydantic import BaseModel
from sqlalchemy import insert
from app.database import get_db, engine
from app.models import collections, requests, params, response
from ..models import requests, BodyType

router = APIRouter()

# Set up the logger
logging.basicConfig(level=logging.INFO)  # You can adjust the level as needed
logger = logging.getLogger(__name__)


class RequestPayload(BaseModel):
    url: str
    method: str
    collection_id: int
    body: str = None
    bodytype: str = None
    param_list: dict = None



@router.delete("/requests/{request_id}")
async def delete_request(request_id: int = Path(..., description="ID of the request to delete"), db: Session = Depends(get_db)):
    try:
        logger.info(f"Deleting request with ID {request_id}")

        # Deleting responses associated with the request
        db.execute(response.delete().where(response.c.request_id == request_id))

        # Deleting params associated with the request
        db.execute(params.delete().where(params.c.request_id == request_id))

        # Deleting the request itself
        delete_result = db.execute(requests.delete().where(requests.c.id == request_id))
        db.commit()

        if delete_result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found")

        return {"detail": "Request and associated data deleted successfully"}

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        db.rollback()  # Rollback the transaction in case of error
        raise HTTPException(status_code=500, detail="Failed to delete request")
 



@router.post("/send_test2")
async def add_request(data: dict):
    body = data.get("body", None)
    params = data.get("params", None)  # Extract params from the input

    # Step 1: Hit the specified URL based on the method
    async with httpx.AsyncClient() as client:
        if data["method"] == "POST":
            response = await client.post(data["url"], json=body)
        elif data["method"] == "GET":
            response = await client.get(data["url"], params=params if params else {})
        elif data["method"] == "PUT":
            # Handle PUT (Update the resource completely)
            response = await client.put(data["url"], json=body)
        elif data["method"] == "PATCH":
            # Handle PATCH (Partial update of resource)
            response = await client.patch(data["url"], json=body)
        elif data["method"] == "DELETE":
            # Handle DELETE (Remove the resource)
            response = await client.delete(data["url"], params=params if params else {})
        else:
            return {"status": "error", "message": "Unsupported HTTP method"}

    # Step 2: Log the response status code
    logger.info(f"Received response: {response.status_code}")

    if response.status_code == 429:
        return {"status": "error", "message": "Too Many Requests. Try again later."}

    # Step 3: Save the request details into the database
    try:
        query = insert(requests).values(
            url=data["url"],
            method=data["method"],
            body=body,
            bodytype=BodyType[data["bodytype"]],
            collection_id=data.get("collection_id", None)
        ).returning(requests.c.id)

        with engine.connect() as conn:
            result = conn.execute(query)
            request_id = result.fetchone()[0]
            conn.commit()  # Ensure changes are committed
            logger.info(f"Inserted request with ID: {request_id}")

        return {
            "status": "success",
            "request_id": request_id,
            "response_status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        logger.error(f"Failed to insert request into the database: {e}")
        raise HTTPException(status_code=500, detail="Failed to save request")






# @router.post("/send_test")
# async def send_request(
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Parse the JSON body
#         data = await request.json()
#         url = data.get("url")
#         method = data.get("method")
#         body = data.get("body")
#         bodytype = data.get("bodytype")
#         collection_id = data.get("collection_id")
#         param_list = data.get("param_list")

#         logger.info(f"Payload: URL={url}, Method={method}, Body={body}, BodyType={bodytype}, CollectionID={collection_id}, Params={param_list}")

#         # Insert new request into the database
#         new_request = requests.insert().values(
#             url=url,
#             method=method,
#             body=body,
#             bodytype=bodytype,
#             collection_id=collection_id
#         )
        
#         logger.info("Inserting new request")
#         result = db.execute(new_request)
#         logger.info(f"Insert result: {result}")

#         db.commit()
#         logger.info("Request committed to database")

#         # Insert parameters (if provided)
#         if param_list:
#             logger.info("Inserting params")
#             for key, value in param_list.items():
#                 new_param = params.insert().values(
#                     key=key,
#                     value=value,
#                     request_id=result.inserted_primary_key[0]
#                 )
#                 db.execute(new_param)
#             db.commit()
#             logger.info("Params committed to database")

#         # Sending the request to the external API
#         response = req.request(method, url, json=body if bodytype == "raw" else None, data=body if bodytype == "form" else None, params=param_list)
#         logger.info(f"Request made to external API. Status: {response.status_code}")

#         return {"status_code": response.status_code, "content": response.content}

#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")



# @router.post("/send_test")
# async def send_request(
#     request: Request,
#     url: str = Form(None), 
#     method: str = Form(None), 
#     body: Optional[str] = Form(None), 
#     bodytype: Optional[str] = Form(None),
#     collection_id: Optional[int] = Form(None),
#     param_list: Optional[Dict[str, str]] = Form(None),
#     db: Session = Depends(get_db)
# ):
#     try:
#         if not url:  # If form data is not provided, assume JSON
#             data = await request.json()
#             url = data.get("url")
#             method = data.get("method")
#             body = data.get("body")
#             bodytype = data.get("bodytype")
#             collection_id = data.get("collection_id")
#             param_list = data.get("param_list")
#         else:
#             logger.info("Received form data payload")
        
#         logger.info(f"Payload: URL={url}, Method={method}, Body={body}, BodyType={bodytype}, CollectionID={collection_id}, Params={param_list}")

#         new_request = requests.insert().values(
#             url=url,
#             method=method,
#             body=body,
#             bodytype=bodytype,
#             collection_id=collection_id
#         )
        
#         logger.info("Inserting new request")
#         result = db.execute(new_request)
#         logger.info(f"Insert result: {result}")

#         db.commit()
#         logger.info("Request committed to database")

#         if param_list:
#             logger.info("Inserting params")
#             for key, value in param_list.items():
#                 new_param = params.insert().values(
#                     key=key,
#                     value=value,
#                     request_id=result.inserted_primary_key[0]
#                 )
#                 db.execute(new_param)
#             db.commit()
#             logger.info("Params committed to database")

#         # Sending the request to the external API
#         response = req.request(method, url, data=body, params=param_list)
#         logger.info(f"Request made to external API. Status: {response.status_code}")
        
#         return {"status_code": response.status_code, "content": response.content}

#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

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
# 
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


# class RequestPayload(BaseModel):
#     url: str
#     method: str
#     body: Optional[str] = None
#     bodytype: Optional[str] = None
#     collection_id: Optional[int] = None
#     param_list: Optional[Dict[str, str]] = None

# @router.post("/send")
# async def send_request(payload: RequestPayload, db: Session = Depends(get_db)):
#     try:
#         logger.info("Received request payload")
#         logger.info(f"Payload: {payload}")

#         new_request = requests.insert().values(
#             url=payload.url,
#             method=payload.method,
#             body=payload.body,
#             bodytype=payload.bodytype,
#             collection_id = payload.collection_id
#         )
        
#         logger.info("Inserting new request")
#         result = db.execute(new_request)
#         logger.info(f"Insert result: {result}")

#         db.commit()
#         logger.info("Request committed to database")

#         if payload.param_list:
#             logger.info("Inserting params")
#             for key, value in payload.param_list.items():
#                 new_param = params.insert().values(
#                     key=key,
#                     value=value,
#                     request_id=result.inserted_primary_key[0]
#                 )
#                 db.execute(new_param)
#             db.commit()
#             logger.info("Params committed to database")

#         response = req.request(payload.method, payload.url, data=payload.body, params=payload.param_list)
#         logger.info(f"Request made to external API. Status: {response.status_code}")
        
#         return {"status_code": response.status_code, "content": response.content}

#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")