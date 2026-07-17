
from fastapi import APIRouter
from app.requests.user_requests import UserRegisterRequest, UserLoginRequest
from app.controllers.user_controller import userObj

from app.models.pg_models import User

user_router = APIRouter(
    tags=["User Router"],
)

@user_router.post("/create-user")
def create_user(user_register_request: UserRegisterRequest):
    return userObj.create_user(user_register_request)
@user_router.post("/login")
def login_user(user_register_request: UserLoginRequest):
    return userObj.login_user(user_register_request)