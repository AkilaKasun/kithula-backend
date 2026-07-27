from decimal import Decimal
from typing import Optional

import jwt
from fastapi import status, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.requests.cart_request import AddToCartRequest,UpdateCartItemRequest

from app.db.postgresDB import db_connection
from app.response.response_model import SuccessResponseModel, ErrorResponseModel
from app.models import pg_models

db: Session = next(db_connection())

class Cart:
    async def add_to_cart(self,request: AddToCartRequest, db: Session):
        try:
            product = (db.query(pg_models.Product).filter(pg_models.Product.product_id == request.product_id,
                                                          pg_models.Product.is_active == True).first())
            if not product:
                return ErrorResponseModel(
                    error="Product not found or unavailable.",
                    code=status.HTTP_404_NOT_FOUND,
                )
            if product.stock < request.quantity:
                return ErrorResponseModel(
                    error=f"Insufficient stock. Available stock: {product.stock}",
                    code=status.HTTP_400_BAD_REQUEST,
                )
            # Get or Create Cart for Customer
            cart = (
                    db.query(pg_models.Cart)
                    .filter(pg_models.Cart.customer_id == request.customer_id)
                    .first()
                )
            if not cart:
                cart = pg_models.Cart(customer_id=request.customer_id)
                db.add(cart)
                db.commit()
                db.refresh(cart)
                db.flush()  # Generates cart_id before commit

            # Check if Product already exists in the Cart
            cart_item = (
                    db.query(pg_models.CartItem)
                    .filter(
                        pg_models.CartItem.cart_id == cart.cart_id,
                        pg_models.CartItem.product_id == request.product_id,
                    )
                    .first()
                )
            if cart_item:
                # Update quantity if already exists
                new_quantity = cart_item.quantity + request.quantity
                if product.stock < new_quantity:
                    return ErrorResponseModel(
                        error=f"Cannot add more. Total limit exceeds available stock ({product.stock}).",
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                cart_item.quantity = new_quantity
            else:
                # Create new CartItem
                cart_item = pg_models.CartItem(
                    cart_id=cart.cart_id,
                    product_id=product.product_id,
                    quantity=request.quantity,
                    price=product.price,  # Snapshot current price
                )
                db.add(cart_item)

            db.commit()
            db.refresh(cart_item)

            return SuccessResponseModel(data={cart_item},
                message="Item added to cart successfully.",
                code=status.HTTP_200_OK,)

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(
                error=f"Failed to add item to cart: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def get_products_in_cart(self, customer_id: str, db: Session):
        try:
            # Query Cart directly by customer_id with joined loading
            cart = (
                db.query(pg_models.Cart)
                .options(
                    joinedload(pg_models.Cart.items)
                    .joinedload(pg_models.CartItem.product)
                    .joinedload(pg_models.Product.image)
                )
                .filter(pg_models.Cart.customer_id == customer_id)
                .first()
            )

            if not cart:
                return SuccessResponseModel(
                    data={"customer_id": customer_id, "items": [], "grand_total": 0.0},
                    message="Cart is empty.",
                    code=status.HTTP_200_OK,
                )

            items_payload = []
            grand_total = Decimal("0.00")

            for item in cart.items:
                item_total = item.price * item.quantity
                grand_total += item_total

                items_payload.append(
                    {
                        "cart_item_id": item.cart_item_id,
                        "product_id": item.product_id,
                        "product_name": item.product.name if item.product else None,
                        "image_url": item.product.image.image_url if item.product and item.product.image else None,
                        "unit_price": float(item.price),
                        "quantity": item.quantity,
                        "subtotal": float(item_total),
                    }
                )

            return SuccessResponseModel(
                data={
                    "cart_id": cart.cart_id,
                    "customer_id": cart.customer_id,
                    "items": items_payload,
                    "grand_total": float(grand_total),
                },
                message="Cart fetched successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to retrieve cart: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def remove_cart_item(self, cart_item_id: int, db: Session):
        try:
            cart_item = (
                db.query(pg_models.CartItem)
                .filter(pg_models.CartItem.cart_item_id == cart_item_id)
                .first()
            )

            if not cart_item:
                return ErrorResponseModel(
                    error="Cart item not found.", code=status.HTTP_404_NOT_FOUND
                )

            db.delete(cart_item)
            db.commit()

            return SuccessResponseModel(
                data={"cart_item_id": cart_item_id},
                message="Cart item removed successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to remove cart item: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def update_cart_item(self,cart_item_id: int, request: UpdateCartItemRequest, db: Session):
        try:
            cart_item = (
                db.query(pg_models.CartItem)
                .options(joinedload(pg_models.CartItem.product))
                .filter(pg_models.CartItem.cart_item_id == cart_item_id)
                .first()
            )

            if not cart_item:
                return ErrorResponseModel(
                    error="Cart item not found.", code=status.HTTP_404_NOT_FOUND
                )

            if cart_item.product and cart_item.product.stock < request.quantity:
                return ErrorResponseModel(
                    error=f"Requested quantity exceeds available stock ({cart_item.product.stock}).",
                    code=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = request.quantity
            db.commit()

            return SuccessResponseModel(
                data={"cart_item_id": cart_item_id, "new_quantity": cart_item.quantity},
                message="Cart item updated successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to update cart item: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )




cartObj=Cart()