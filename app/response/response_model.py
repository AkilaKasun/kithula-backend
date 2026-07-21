from datetime import datetime, timezone

from fastapi import status


def SuccessResponseModel(data, message, code=status.HTTP_200_OK):
    return {
        "status": True,
        "data": data,
        "code": code,
        "message": message
    }

def ErrorResponseModel(
    error="server error",
    code=status.HTTP_400_BAD_REQUEST,
    error_code="INTERNAL_ERROR",
    details=None
):
    return {
        "status": False,
        "data": None,
        "code": code,
        "error_code": error_code,
        "message": error,
        "details": details or [],
        "timestamp": datetime.now(datetime.UTC).isoformat()
    }