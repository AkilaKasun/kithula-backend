
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.db.postgresDB import db_connection
from app.models import pg_models
from app.requests.product_requests import ProductCreateRequest
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
    """
    Creates a new product record.
    - Parses text/form inputs into ProductCreateRequest.
    - Receives product image file payload.
    - Controller handles image upload to S3 and input validations.
    """
    return await productObj.create_product(
        request=request,
        file=file,
        db=db,
        current_user=current_user
    )
