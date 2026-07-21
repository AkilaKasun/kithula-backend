from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.db.postgresDB import db_connection
from app.models import pg_models
from app.requests.product_requests import ProductCreateRequest, ProductUpdateRequest
from app.controllers.product_controller import productObj


product_router = APIRouter(
    tags=["Product Router"],
)


@product_router.post("/create-product")
async def create_product_route(
    request: ProductCreateRequest = Depends(ProductCreateRequest.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(db_connection),
    current_user: pg_models.User = Depends(get_current_user)
):

    return await productObj.create_product(
        request=request,
        file=file,
        db=db,
        current_user=current_user
    )

@product_router.get("/all-products")
async def get_all_products(db: Session = Depends(db_connection)):
    return await productObj.get_all_products(db=db)


@product_router.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(db_connection)):
    return await productObj.get_product_by_id(product_id=product_id, db=db)


@product_router.put("/update-product/{product_id}")
async def update_product(product_id: int, request: ProductUpdateRequest = Depends(ProductUpdateRequest.as_form),file: Optional[UploadFile] = File(None),
    db: Session = Depends(db_connection),
    current_user: pg_models.User = Depends(get_current_user),):
    return await productObj.update_product(
        product_id=product_id,
        request=request,
        db=db,
        current_user=current_user,
        file=file,
    )
@product_router.delete("/delete-product/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(db_connection),current_user: pg_models.User = Depends(get_current_user)):
    return await productObj.delete_product(product_id=product_id,
        db=db,
        current_user=current_user,)
