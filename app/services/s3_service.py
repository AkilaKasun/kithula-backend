import uuid
import aioboto3
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError
from app.config import settings

# Initialize a global Async Session
session = aioboto3.Session()


async def upload_image(file: UploadFile) -> str:
    """
    Asynchronously uploads a product image file to the configured AWS S3 bucket.
    Uses aioboto3 to prevent blocking the FastAPI event loop during file I/O operations.
    """
    # 1. Generate a unique safe filename
    filename = f"products/{uuid.uuid4()}-{file.filename}"

    try:
        # 2. Open an asynchronous client context manager
        async with session.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
        ) as s3_client:

            # 3. Read the file payload asynchronously
            file_content = await file.read()

            # 4. Upload using the async put_object method
            await s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=filename,
                Body=file_content,
                ContentType=file.content_type
            )

        # 5. Construct and return the absolute public URL
        return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AWS S3 Cloud Upload Failure: {e.response['Error']['Message']}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during image upload: {str(e)}"
        )
async def delete_image_from_s3(s3_key: str) -> bool:
    """
    Asynchronously deletes an object from AWS S3 using its S3 Key.
    Uses aioboto3 to prevent blocking the FastAPI event loop.
    """
    if not s3_key:
        return False

    try:
        async with session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:

            await s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key,
            )

        return True

    except ClientError as e:
        print(f"AWS S3 Cloud Deletion Failure: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during S3 deletion: {str(e)}")
        return False