from app.models.pg_models import Base
from app.db.postgresDB import engine



def init_model():
    Base.metadata.create_all(bind=engine) #create databases