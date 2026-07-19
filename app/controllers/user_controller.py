import jwt
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.auth import hash_password, verify_password, create_access_token
from app.db.postgresDB import db_connection
from app.response.response_model import SuccessResponseModel, ErrorResponseModel
from app.models import pg_models

db: Session = next(db_connection())


class User():
    def create_user(self, request):
        try:
            existing_user = db.query(pg_models.User).filter(
                (pg_models.User.email == request.email) | (pg_models.User.username == request.username)
            ).first()
            if existing_user:
                return ErrorResponseModel(error="Username or Email already registered.",
                                          code=status.HTTP_400_BAD_REQUEST)

            new_user = pg_models.User(
                username=request.username,
                email=request.email,
                hashed_password=hash_password(request.password),
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Fixed parameter placement: data first, then message, then custom code
            return SuccessResponseModel(data=new_user, message="User created successfully.", code=status.HTTP_201_CREATED)

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(error=str(e), code=status.HTTP_400_BAD_REQUEST)

    def login_user(self, request, db: Session):
        try:
            user = db.query(pg_models.User).filter(pg_models.User.username == request.username).first()

            if not user or not verify_password(request.password, user.hashed_password):
                return ErrorResponseModel(error="Invalid username or password.", code=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                user.is_active = True
                db.commit()
                db.refresh(user)

            token_payload = {"sub": str(user.user_id)}
            access_token = create_access_token(data=token_payload)

            # CRITICAL: Return a completely flat dictionary layout at the root level
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email
                }
            }

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(error=str(e), code=status.HTTP_400_BAD_REQUEST)



    # def login_user(self, request):
    #     try:
    #         user = db.query(pg_models.User).filter(pg_models.User.username == request.username).first()
    #
    #         # Unified handling to use ErrorResponseModel directly instead of raising raw FastAPIs exceptions
    #         if not user or not verify_password(request.password, user.hashed_password):
    #             return ErrorResponseModel(error="Invalid username or password.", code=status.HTTP_401_UNAUTHORIZED)
    #
    #         if not user.is_active:
    #             return ErrorResponseModel(error="This account has been deactivated.", code=status.HTTP_403_FORBIDDEN)
    #
    #         token_payload = {"sub": str(user.username)}
    #         access_token = create_access_token(data=token_payload)
    #
    #         data_payload = {
    #             "access_token": access_token,
    #             "token_type": "bearer",
    #             "user": {
    #                 "id": user.id,
    #                 "username": user.username,
    #                 "email": user.email
    #             }
    #         }
    #
    #         return SuccessResponseModel(data=data_payload, message="Login successful.")
    #
    #     except Exception as e:
    #         print(str(e))
    #         return ErrorResponseModel(error=str(e), code=status.HTTP_400_BAD_REQUEST)
    from fastapi import status, HTTPException
    from sqlalchemy.orm import Session

    def logout_user(self, db: Session, current_user):
        try:
            # 1. Find the user in the database using the passed db session
            db_user = db.query(pg_models.User).filter(pg_models.User.user_id == current_user.user_id).first()
            if not db_user:
                return ErrorResponseModel(error="User not found.", code=status.HTTP_404_NOT_FOUND)

            # 2. Make the user inactive
            db_user.is_active = False
            db.commit()
            db.refresh(db_user)

            return SuccessResponseModel(data=None, message="Logout successful.")

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(error=str(e), code=status.HTTP_400_BAD_REQUEST)

    def get_user_by_id(self, user_id: int, current_user: pg_models.User, db: Session):
        try:
            # 1. Check if the executing user is active
            if not current_user.is_active:
                return ErrorResponseModel(error="Your account is deactivated.", code=status.HTTP_403_FORBIDDEN)

            # 2. Query target user using the injected db session
            user = db.query(pg_models.User).filter(pg_models.User.user_id == user_id).first()
            if not user:
                return ErrorResponseModel(error="User not found.", code=status.HTTP_404_NOT_FOUND)

            # 3. Build response payload
            data = {
                "id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": str(user.created_at)  # Converted to string for JSON serialization safety
            }

            return SuccessResponseModel(data=data, message="User retrieved successfully.")

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(error=str(e), code=status.HTTP_400_BAD_REQUEST)


userObj = User()