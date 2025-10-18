from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.Config.database import get_db_session
from src.API.Controllers import auth_controller
from src.Schemas.auth_schema import AuthResponse, CreateUser, UserLogin

router = APIRouter()

@router.post("/register",
    response_model = auth_controller.AuthResponse,
    status_code=status.HTTP_201_CREATED)
def register_user(newUser : CreateUser, db: Session = Depends(get_db_session)):
    try:
        return auth_controller.create_user(newUser, db)
    except Exception as e:
        print(f"Error creating user: {e}")
        return {"status": "error", "message": f"Error creating user: {e}", "token": None}
    
@router.post("/login",
        response_model=auth_controller.AuthResponse,
        status_code=status.HTTP_200_OK,
        description="Route to login a user. Returns a JWT token.")
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db_session)):
    try:
        return auth_controller.login_user(user_credentials, db)
    except Exception as e:
        print(f"Error logging in user: {e}")
        return {"status": "error", "message": f"Error logging in user: {e}" , "token": None}