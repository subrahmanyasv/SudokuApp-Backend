from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.Config.database import get_db_session
from src.Security.security import validate_user
from src.Schemas.user_schema import UserData, User as baseUser, UserResponse
from src.Schemas.auth_schema import TokenPayload
from src.API.Controllers import user_controller

router = APIRouter()

@router.get("/",
    response_model = UserResponse,
    status_code=status.HTTP_200_OK)
def get_user(user : TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session)):
    try:
        user =  user_controller.get_user_data(user.id, db)
        response = {
            "status": "success",
            "message": user
        }

        return response
    except Exception as e:
        print(f"Error getting user: {e}")
        return {"status": "error", "message": f"Error getting user: {e}"}

