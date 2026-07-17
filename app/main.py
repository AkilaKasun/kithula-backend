from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from app.db import init_model
from app.db.postgresDB import db_connection

from app.routers.user_routes import user_router
@asynccontextmanager
async def lifespan(app: FastAPI): #start app fast api
    init_model() #call database creation
    yield #shutdown app after the database creation


app = FastAPI(
        title="Kithula ",
        lifespan=lifespan, #call init model and create database models

)

app.include_router(user_router)

@app.get("/")
def home():
    return {"message": "API Running"}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)