
from sqlalchemy import Column, Integer, String, create_engine, UUID, DateTime, func, Numeric, ForeignKey

from app.db.postgresDB import Base

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)



class product(Base):
    __tablename__ = 'product'
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
