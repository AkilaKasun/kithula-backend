from decimal import Decimal
from typing import Optional
from fastapi import Form
from pydantic import BaseModel


class ProductCreateRequest(BaseModel):
    name: str
    description: str
    price: Decimal
    stock: int
    category: str
    file_id: Optional[str] = None  # Populated internally after S3 upload

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: str = Form(...),
        price: Decimal = Form(...),
        stock: int = Form(...),
        category: str = Form(...)
    ):
        return cls(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category
        )
class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

    @classmethod
    def as_form(
        cls,
        name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[Decimal] = Form(None),
        stock: Optional[int] = Form(None),
        category: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
    ):
        return cls(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            is_active=is_active,
        )