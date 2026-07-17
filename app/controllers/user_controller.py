import jwt
from sqlalchemy.orm import Session

from app.auth.auth import hash_password, verify_password, create_access_token
from app.db.postgresDB import db_connection
from app.response.response_model import SuccessResponseModel, ErrorResponseModel
from app.models import pg_models

db:Session = next(db_connection())

class User():
    def create_user(self,request):
        try:
            existing_user = db.query(pg_models.User).filter(
                (pg_models.User.email == request.email) | (pg_models.User.username == request.username)
            ).first()
            if existing_user:
                return ErrorResponseModel("Username or Email already registered.",400)

            new_user = pg_models.User(
                username=request.username,
                email=request.email,
                hashed_password = hash_password(request.password),
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return SuccessResponseModel("User created successfully.",201)

        except Exception as e:
            print(str(e))
            return ErrorResponseModel(str(e), 400)



    def login_user(self,request):
        try:
            user = db.query(pg_models.User).filter(pg_models.User.username==request.username).first()

            if not user or not verify_password(request.password,user.hashed_password):
                return ErrorResponseModel("Username or Password Incorrect.",400)

            token_payload = {"sub": str(user.username)}
            access_token = create_access_token(data=token_payload)

            data_payload = {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }

            # Matches SuccessResponseModel(data, message)
            return SuccessResponseModel(
                data=data_payload,
                message="Login successful."
            )
        except Exception as e:
            print(str(e))
            return ErrorResponseModel(str(e), 400)

userObj = User()


