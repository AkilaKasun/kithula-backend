from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class AddToCartRequest(BaseModel):
    customer_id: str = Field(..., description="Unique frontend token or UUID for customer session")
    product_id: int = Field(..., description="ID of the product being added")
    quantity: int = Field(1, ge=1, description="Quantity to add (Must be at least 1)")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1, description="New quantity for the cart item")