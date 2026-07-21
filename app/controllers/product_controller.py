from decimal import Decimal
from typing import Optional

import jwt
from fastapi import status, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.requests.product_requests import ProductCreateRequest, ProductUpdateRequest
from app.services.s3_service import upload_image, delete_image_from_s3

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

    async def get_all_products(self, db: Session):
        """
        Retrieves all active products with linked image and creator details.
        No user authentication required.
        """
        try:
            products = (
                db.query(pg_models.Product)
                .options(
                    joinedload(pg_models.Product.image),
                    joinedload(pg_models.Product.creator),
                )
                .filter(pg_models.Product.is_active == True)
                .all()
            )

            # Convert SQLAlchemy objects to JSON-serializable dictionaries
            products_data = [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "description": p.description,
                    "price": float(p.price),
                    "stock": p.stock,
                    "category": p.category,
                    "is_active": p.is_active,
                    "image_url": p.image.image_url if p.image else None,# Fetch image_url safely from the linked 'image' relationship
                    "created_by": p.created_by,
                    "created_at": p.created_at.isoformat()
                    if p.created_at
                    else None,
                    "updated_at": p.updated_at.isoformat()
                    if p.updated_at
                    else None,
                    "image_details": {
                        "file_name": p.image.file_name,
                        "s3_key": p.image.s3_key,
                        "bucket_name": p.image.bucket_name,
                    }
                    if p.image
                    else None,
                }
                for p in products
            ]

            return SuccessResponseModel(
                data=products_data,
                message="Products retrieved successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to fetch products: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def get_product_by_id(self, product_id: int, db: Session):

        try:
            product = (
                db.query(pg_models.Product)
                .options(
                    joinedload(pg_models.Product.image),
                    joinedload(pg_models.Product.creator),
                )
                .filter(pg_models.Product.product_id == product_id)
                .first()
            )

            if not product:
                return ErrorResponseModel(
                    error=f"Product with ID {product_id} not found.",
                    code=status.HTTP_404_NOT_FOUND,
                )

            product_data = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "stock": product.stock,
                "category": product.category,
                "is_active": product.is_active,
                "image_url": product.image.image_url if product.image else None, # Fetch image_url safely from the linked 'image' relationship
                "created_by": product.created_by,
                "created_at": product.created_at.isoformat()
                if product.created_at
                else None,
                "updated_at": product.updated_at.isoformat()
                if product.updated_at
                else None,
                "image_details": {
                    "file_name": product.image.file_name,
                    "s3_key": product.image.s3_key,
                    "bucket_name": product.image.bucket_name,
                }
                if product.image
                else None,
            }

            return SuccessResponseModel(
                data=product_data,
                message="Product retrieved successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to fetch product: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def update_product(self,product_id: int,
        request: ProductUpdateRequest,
        db: Session,
        current_user: pg_models.User ,
        file: Optional[UploadFile] = None,):
        try:
            if not current_user:
                return ErrorResponseModel(
                    error="Unauthorized: Authentication required.",
                    code=status.HTTP_401_UNAUTHORIZED,
                )

                # 2. Fetch existing product
            product = (
                db.query(pg_models.Product)
                .options(
                    joinedload(pg_models.Product.image),
                    joinedload(pg_models.Product.creator),
                )
                .filter(pg_models.Product.product_id == product_id)
                .first()
            )

            if not product:
                return ErrorResponseModel(
                    error=f"Product with ID {product_id} not found.",
                    code=status.HTTP_404_NOT_FOUND,
                )
            if file and file.filename:
                file_storage_record = await self.file_upload(file=file, db=db)
                product.file_id = file_storage_record.file_id

            '''Pydantic V2 හි model_dump(exclude_unset=True) මගින් request එකේ Client විසින් පැහැදිලිවම එවන ලද Fields පමණක් Dictionary එකක් ලෙස ලබා ගනී.'''
            update_data = request.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(product, key, value)

            db.commit()
            db.refresh(product)

            updated_product_data = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "stock": product.stock,
                "category": product.category,
                "is_active": product.is_active,
                "file_id": product.file_id,
                "image_url": product.image.image_url if product.image else None,
                "created_by": product.created_by,
                "created_at": product.created_at.isoformat()
                if product.created_at
                else None,
                "updated_at": product.updated_at.isoformat()
                if product.updated_at
                else None,
                "image_details": {
                    "file_name": product.image.file_name,
                    "s3_key": product.image.s3_key,
                    "bucket_name": product.image.bucket_name,
                }
                if product.image
                else None,
            }

            return SuccessResponseModel(
                data=updated_product_data,
                message="Product updated successfully.",
                code=status.HTTP_200_OK,
            )


        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to update product: {str(e)}",
            )

    async def delete_product(
            self, product_id: int, db: Session, current_user: pg_models.User
    ):
        try:
            # 1. Authentication Check
            if not current_user:
                return ErrorResponseModel(
                    error="Unauthorized: Authentication required.",
                    code=status.HTTP_401_UNAUTHORIZED,
                )

            # 2. Fetch product and eager load its image relationship
            product = (
                db.query(pg_models.Product)
                .options(joinedload(pg_models.Product.image))
                .filter(pg_models.Product.product_id == product_id)
                .first()
            )

            if not product:
                return ErrorResponseModel(
                    error=f"Product with ID {product_id} not found.",
                    code=status.HTTP_404_NOT_FOUND,
                )

            # 3. Store reference to the attached image before deleting product
            image_record = product.image

            # 4. Delete the product first (clears FK dependency on file_storage)
            db.delete(product)

            # 5. Delete associated FileStorage record and S3 file
            if image_record:
                # Extract s3_key before deleting from DB
                s3_key = image_record.s3_key

                db.delete(image_record)

                # Delete file asynchronously from AWS S3 bucket
                if s3_key:
                    await delete_image_from_s3(s3_key)

            # 6. Commit database changes
            db.commit()

            return SuccessResponseModel(
                data={"product_id": product_id},
                message="Product, image record, and S3 file deleted successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to delete product: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

productObj = Product()