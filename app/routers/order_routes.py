from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.controllers.order_controller import orderObj
from app.db.postgresDB import db_connection
from app.models import pg_models
from app.requests.order_requests import CreateOrderRequest, UpdateOrderStatusRequest

order_router = APIRouter( tags=["Orders"])

@order_router.post("/create-order")
async def checkout(
    request: CreateOrderRequest, db: Session = Depends(db_connection)
):
    return await orderObj.create_order(request, db)

@order_router.get("/get-all-orders")
async def get_all_orders(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(10, ge=1, le=500, description="Limit for pagination"),
    db: Session = Depends(db_connection),
):
    return await orderObj.get_all_orders(db=db, limit=limit, skip=skip)

@order_router.get("/get-orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(db_connection)):
    return await orderObj.get_order_by_id(order_id=order_id, db=db)

@order_router.patch("/order-status/{order_id}")
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(db_connection),
):
    return await orderObj.update_order_status(order_id, request, db)

@order_router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    db: Session = Depends(db_connection),
    current_user: pg_models.User = Depends(get_current_user),
):
    return await orderObj.delete_order(order_id=order_id, db=db, current_user=current_user,)