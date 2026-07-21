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