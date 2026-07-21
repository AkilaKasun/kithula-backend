from decimal import Decimal

import jwt
from fastapi import status, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.requests.product_requests import ProductCreateRequest
from app.services.s3_service import upload_image

from app.auth.auth import hash_password, verify_password, create_access_token
from app.db.postgresDB import db_connection
from app.response.response_model import SuccessResponseModel, ErrorResponseModel
from app.models import pg_models

db: Session = next(db_connection())

class Product():
    async def file_upload(self, file: UploadFile, db: Session) -> pg_models.FileStorage:
        """
        Uploads an image to S3 using s3_service and records its metadata in FileStorage table.
        """
        # 1. Upload image to S3 asynchronously
        image_url = await upload_image(file)

        # Extract S3 key
        s3_key = image_url.split(f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/")[-1]

        # 2. Save metadata to FileStorage table
        file_storage_record = pg_models.FileStorage(
            file_name=file.filename,
            s3_key=s3_key,
            image_url=image_url,
            bucket_name=settings.AWS_BUCKET_NAME
        )
        db.add(file_storage_record)
        db.commit()
        db.refresh(file_storage_record)

        return file_storage_record

    async def create_product(
            self,
            request: ProductCreateRequest,
            file: UploadFile,
            db: Session,
            current_user: pg_models.User
    ):
        if not file:
            return ErrorResponseModel(
                error="Product image file is required.",
                code=status.HTTP_400_BAD_REQUEST
            )
        if not request.name or not request.name.strip():
            return ErrorResponseModel(
                error="Product name is required and cannot be empty.",
                code=status.HTTP_400_BAD_REQUEST
            )

        if request.price <= Decimal("0"):
            return ErrorResponseModel(
                error="Product price must be greater than 0.",
                code=status.HTTP_400_BAD_REQUEST
            )

        if request.stock < 0:
            return ErrorResponseModel(
                error="Product stock cannot be negative.",
                code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Call the separate file_upload helper function
            file_storage_record = await self.file_upload(file=file, db=db)

            # 2. Create Product using request payload and file_storage_record image_url FK
            new_product = pg_models.Product(
                name=request.name,
                description=request.description,
                price=request.price,
                stock=request.stock,
                category=request.category,
                file_id=file_storage_record.file_id,
                created_by=current_user.user_id
            )

            db.add(new_product)
            db.commit()
            db.refresh(new_product)

            return SuccessResponseModel(
                data={
                    "product_id": new_product.product_id,
                    "name": new_product.name,
                    "description": new_product.description,
                    "price": float(new_product.price),
                    "stock": new_product.stock,
                    "category": new_product.category,
                    "file_id": new_product.file_id,
                    "created_by": new_product.created_by
                },
                message="Product created successfully.",
                code=status.HTTP_201_CREATED
            )

        except HTTPException as http_ex:
            db.rollback()
            return ErrorResponseModel(error=http_ex.detail, code=http_ex.status_code)
        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to create product: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST
            )

productObj = Product()