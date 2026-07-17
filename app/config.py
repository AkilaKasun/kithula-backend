import os
import boto3
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Database Settings
    POSTGRES_USERNAME: str = os.getenv("POSTGRES_USERNAME")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    DB_CONNECTION: str = os.getenv("DB_CONNECTION", "postgresql")

    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "kithula1-s3-storage1")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")

    #JWT SECRET KEYS
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"{self.DB_CONNECTION}://{self.POSTGRES_USERNAME}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

settings = Settings()

# Centralized Boto3 S3 Client Instance
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)