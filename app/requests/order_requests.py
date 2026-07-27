from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class CreateOrderRequest(BaseModel):
    customer_id: str = Field(..., description="UUID or session token of the cart owner")
    customer_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    district: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., description="Pending, Confirmed, Preparing, Ready, Delivered, Cancelled")