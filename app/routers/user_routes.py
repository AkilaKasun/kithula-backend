
from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.db.postgresDB import db_connection
from app.models import pg_models
from app.requests.user_requests import UserRegisterRequest, UserLoginRequest
from app.controllers.user_controller import userObj

from app.models.pg_models import User

user_router = APIRouter(
    tags=["User Router"],
)

@user_router.post("/create-user")
def create_user(user_register_request: UserRegisterRequest):
    return userObj.create_user(user_register_request)

#
# @user_router.post("/login")
# def login_user(user_register_request: UserLoginRequest):
#     return userObj.login_user(user_register_request)

@user_router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(db_connection)
):
    return userObj.login_user(form_data, db)

@user_router.post("/logout")
def logout_user(
    db: Session = Depends(db_connection),
    current_user: pg_models.User = Depends(get_current_user)
):
    return userObj.logout_user(db=db, current_user=current_user)

@user_router.get("/me")
def get_logged_in_user(
    current_user: pg_models.User = Depends(get_current_user),
    db: Session = Depends(db_connection)
):
    # Pass current_user.id as the target id to reuse the get_user_by_id logic cleanly
    return userObj.get_user_by_id(user_id=current_user.user_id, current_user=current_user, db=db)

@user_router.delete("/delete-user/{user_id}")
def delete_user(user_id: int):
    return userObj.delete_user(user_id=user_id)