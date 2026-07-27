from decimal import Decimal
from fastapi import status
from sqlalchemy.orm import Session, joinedload


from app.models import pg_models
from app.requests.order_requests import CreateOrderRequest,UpdateOrderStatusRequest
from app.response.response_model import ErrorResponseModel, SuccessResponseModel


import jwt
from fastapi import status, HTTPException, UploadFile



class Order:
    async def create_order(self,request: CreateOrderRequest,db: Session):
        try:

            # 1. Validate Email (@ symbol check)
            if not request.email or "@" not in request.email:
                return ErrorResponseModel(
                    error="Invalid email address. Email must contain an '@' symbol.",
                    code=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Validate Phone Number (10 digits check)
            clean_phone = request.phone.strip() if request.phone else ""
            if not clean_phone.isdigit() or len(clean_phone) != 10:
                return ErrorResponseModel(
                    error="Invalid phone number. Phone number must contain exactly 10 digits.",
                    code=status.HTTP_400_BAD_REQUEST,
                )

            cart = (
                db.query(pg_models.Cart)
                .options(
                    joinedload(pg_models.Cart.items).joinedload(pg_models.CartItem.product)
                )
                .filter(pg_models.Cart.customer_id == request.customer_id)
                .first()
            )
            if not cart or not cart.items:
                return ErrorResponseModel(
                    error="Your cart is empty or does not exist.",
                    code=status.HTTP_400_BAD_REQUEST,
                )
            #  CALCULATE TOTAL & PREPARE ORDER ITEMS
            total_amount = Decimal("0.00")
            order_items_to_create = []

            for cart_item in cart.items:
                # Row lock product to prevent race conditions during stock check
                product = (
                    db.query(pg_models.Product)
                    .filter(
                        pg_models.Product.product_id == cart_item.product_id,
                        pg_models.Product.is_active == True,
                    )
                    .with_for_update()
                    .first()
                )

                if not product:
                    db.rollback()
                    return ErrorResponseModel(
                        error=f"Product with ID {cart_item.product_id} is no longer available.",
                        code=status.HTTP_400_BAD_REQUEST,
                    )

                if product.stock < cart_item.quantity:
                    db.rollback()
                    return ErrorResponseModel(
                        error=f"Insufficient stock for '{product.name}'. Available: {product.stock}, requested: {cart_item.quantity}.",
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                # Deduct stock directly from Product table
                product.stock -= cart_item.quantity

                # CALCULATE ITEM TOTAL AND ACCUMULATE GRAND TOTAL
                item_price = Decimal(str(product.price))
                item_total = item_price * cart_item.quantity
                total_amount += item_total

                # Prepare OrderItem (snapshot price at time of purchase)
                order_items_to_create.append(
                    pg_models.OrderItem(
                        product_id=product.product_id,
                        quantity=cart_item.quantity,
                        price=item_price,
                    )
                )

                #  CREATE ORDER (No user_id or cart_id saved in the table)
                new_order = pg_models.Order(
                    customer_name=request.customer_name,
                    phone=request.phone,
                    email=request.email,
                    address_line1=request.address_line1,
                    address_line2=request.address_line2,
                    district=request.district,
                    postal_code=request.postal_code,
                    notes=request.notes,
                    total_amount=total_amount,  # Calculated sum
                    status="Pending",
                    items=order_items_to_create,
                )

                db.add(new_order)

                # CLEANUP: Clear guest's cart items and delete cart after order placement
                for cart_item in cart.items:
                    db.delete(cart_item)
                db.delete(cart)

                db.commit()
                db.refresh(new_order)

                return SuccessResponseModel(
                    data={
                        "order_id": new_order.order_id,
                        "total_amount": float(new_order.total_amount),
                        "status": new_order.status,
                        "created_at": new_order.created_at.isoformat() if new_order.created_at else None,
                    },
                    message="Order placed successfully.",
                    code=status.HTTP_201_CREATED,
                )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Checkout failed: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def get_all_orders(self, db: Session, limit: int = 10, skip: int = 0):
        try:

            total_orders = db.query(pg_models.Order).count()


            orders = (
                db.query(pg_models.Order)
                .options(
                    joinedload(pg_models.Order.items).joinedload(
                        pg_models.OrderItem.product
                    )
                )
                .order_by(pg_models.Order.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )


            orders_payload = [
                {
                    "order_id": order.order_id,
                    "customer_name": order.customer_name,
                    "phone": order.phone,
                    "email": order.email,
                    "shipping_address": {
                        "address_line1": order.address_line1,
                        "address_line2": order.address_line2,
                        "district": order.district,
                        "postal_code": order.postal_code,
                    },
                    "notes": order.notes,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "items": [
                        {
                            "order_item_id": item.order_item_id,
                            "product_id": item.product_id,
                            "product_name": item.product.name if item.product else "N/A",
                            "quantity": item.quantity,
                            "unit_price": float(item.price),
                            "subtotal": float(item.price * item.quantity),
                        }
                        for item in order.items
                    ],
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                }
                for order in orders
            ]


            return SuccessResponseModel(
                data={
                    "total_count": total_orders,
                    "retrieved_count": len(orders_payload),
                    "skip": skip,
                    "limit": limit,
                    "orders": orders_payload,
                },
                message="All orders retrieved successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to fetch orders: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def get_order_by_id(self, db: Session, order_id: int):
        try:
            order = db.query(pg_models.Order).options(
                    joinedload(pg_models.Order.items).
                    joinedload(pg_models.OrderItem.product)
                ).filter(pg_models.Order.order_id == order_id).first()
            if not order:
                return ErrorResponseModel(
                    error="Order not found.", code=status.HTTP_404_NOT_FOUND
                )
            items_payload = [
                {
                    "order_id": order.order_id,
                    "customer_name": order.customer_name,
                    "phone": order.phone,
                    "email": order.email,
                    "shipping_address": {
                        "address_line1": order.address_line1,
                        "address_line2": order.address_line2,
                        "district": order.district,
                        "postal_code": order.postal_code,
                    },
                    "notes": order.notes,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "order_item_id": item.order_item_id,
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else "N/A",
                    "quantity": item.quantity,
                    "unit_price": float(item.price),
                    "subtotal": float(item.price * item.quantity),
                }
                for item in order.items
            ]

            return SuccessResponseModel(
                data={"items": items_payload},
                message="Order retrieved successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            return ErrorResponseModel(
                error=f"Failed to fetch order: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def update_order_status(self, order_id: int, request: UpdateOrderStatusRequest, db: Session):
        try:
            order = db.query(pg_models.Order).filter(pg_models.Order.order_id == order_id).first()

            if not order:
                return ErrorResponseModel(
                    error="Order not found.", code=status.HTTP_404_NOT_FOUND
                )

            order.status = request.status
            db.commit()
            db.refresh(order)

            return SuccessResponseModel(
                data={"order_id": order.order_id, "status": order.status},
                message=f"Order status updated to '{order.status}'.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to update order status: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )

    async def delete_order(self, order_id: int, db: Session, current_user: pg_models.User ):
        try:

            if not current_user:
                return ErrorResponseModel(
                    error="Unauthorized: Authentication required.",
                    code=status.HTTP_401_UNAUTHORIZED,
                )

            order = (
                db.query(pg_models.Order)
                .filter(pg_models.Order.order_id == order_id)
                .first()
            )

            if not order:
                return ErrorResponseModel(
                    error="Order not found.",
                    code=status.HTTP_404_NOT_FOUND,
                )

            # 2. Status validation: allow deletion only if Delivered or Cancelled
            allowed_statuses = ["Delivered", "Cancelled"]
            if order.status not in allowed_statuses:
                return ErrorResponseModel(
                    error=f"Cannot delete order with status '{order.status}'. Only 'Delivered' or 'Cancelled' orders can be deleted.",
                    code=status.HTTP_400_BAD_REQUEST,
                )

            # 3. Delete related items and the order
            for item in order.items:
                db.delete(item)

            db.delete(order)
            db.commit()

            return SuccessResponseModel(
                data={"order_id": order_id},
                message=f"Order #{order_id} deleted successfully.",
                code=status.HTTP_200_OK,
            )

        except Exception as e:
            db.rollback()
            return ErrorResponseModel(
                error=f"Failed to delete order: {str(e)}",
                code=status.HTTP_400_BAD_REQUEST,
            )


orderObj = Order()