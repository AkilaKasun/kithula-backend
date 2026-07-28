from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from app.db import init_model
from app.db.postgresDB import db_connection
from app.middleware.cors import setup_cors

from app.routers.user_routes import user_router
from app.routers.product_routes import product_router
from app.routers.cart_routes import cart_router
from app.routers.order_routes import order_router

@asynccontextmanager
async def lifespan(app: FastAPI): #start app fast api
    init_model() #call database creation
    yield #shutdown app after the database creation


app = FastAPI(
        title="Kithula ",
        lifespan=lifespan, #call init model and create database models

)
# Call the separate middleware function
setup_cors(app)

app.include_router(user_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)

@app.get("/")
def home():
    return {"message": "API Running"}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)