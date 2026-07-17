
from sqlalchemy import Column, Integer, String, create_engine, UUID, DateTime, func, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.postgresDB import Base

#AUTHENTICATION MODULE (Admin Only)
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

#IMAGE UPLOAD
class FileStorage(Base):
    __tablename__ = 'file_storage'

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)      # Original name (e.g., "kithul_podi.png")
    s3_key = Column(String(500), nullable=False, unique=True) # Unique S3 path/key for deletion tracking
    image_url = Column(String(500), nullable=False)     # Public URL used to display the image on the frontend
    bucket_name = Column(String(100), nullable=False)   # Target bucket name (e.g., kithula1-s3-storage1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

#PRODUCT MODULE
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    category = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Foreign Key pointing to the FileStorage table
    file_id = Column(Integer, ForeignKey('file_storage.id', ondelete='SET NULL'), nullable=True)
    # Changed ondelete from 'SET NULL' to 'CASCADE'
    created_by = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=True)


    # Relationship remains the same
    creator = relationship("User")
    # Relationship to cleanly pull image details
    image = relationship("FileStorage")

#CART MODULE
class Cart(Base):
    __tablename__ = 'carts'

    cart_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), unique=True, nullable=False, index=True)  # Frontend generated UUID token
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Deleting a cart drops all associated items automatically
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric(10, 2), nullable=False)  # Snapshot of price when added

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")  # Uni-directional lookup: item -> details


 # CHECKOUT & ORDER MODULES (COD Only)

class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True, index=True)

    # Customer Details
    customer_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)

    # Updated Shipping Snapshot Layout
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)  # Explicitly optional
    district = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    notes = Column(String(500), nullable=True)

    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="Pending")  # Pending, Confirmed, Preparing, Ready, Delivered, Cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Immutable historical purchase price

    order = relationship("Order", back_populates="items")
    product = relationship("Product")  # Uni-directional lookup: item -> details