from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.postgresDB import db_connection
from app.controllers.cart_controller import cartObj
from app.requests.cart_request import AddToCartRequest,UpdateCartItemRequest

cart_router = APIRouter( tags=["Cart"])

@cart_router.post("/add-to-cart")
async def add_to_cart(
    request: AddToCartRequest, db: Session = Depends(db_connection)
):
    return await cartObj.add_to_cart(request, db)

@cart_router.get("/get-all-cart-items/{customer_id}")
async def get_cart(customer_id: str, db: Session = Depends(db_connection)):
    return await cartObj.get_products_in_cart(customer_id, db)

@cart_router.delete("/remove-from-cart")
async def remove_from_cart(cart_item_id: str, db: Session = Depends(db_connection)):
    return await cartObj.remove_from_cart(cart_item_id, db)

@cart_router.put("/update-cart/{cart_item_id}")
async def update_cart(cart_item_id:str, request: UpdateCartItemRequest, db: Session = Depends(db_connection)):
    return await cartObj.update_cart_item(cart_item_id, request, db)