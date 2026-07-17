from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Create Engine using the settings object property
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_size=50,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

# Session Factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base Class
Base = declarative_base()


# Dependency
def db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()