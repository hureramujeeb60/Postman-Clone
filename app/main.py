from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import request_routes
from app.routes import collection_routes
from app.routes import response_routes
from app.routes import param_routes
from .database import database, engine, Base, metadata
from .models import collections, requests, params

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )
1
app.include_router(request_routes.router, prefix="/api")
app.include_router(collection_routes.router, prefix="/api")
app.include_router(response_routes.router, prefix="/api")
app.include_router(param_routes.router, prefix="/api")

async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()


@app.get("/")
def read_root():
    return {"message": "Welcome to your Postman Clone API!"}

@app.get("/ping")
def ping():
    return {"ping": "pong!"}
