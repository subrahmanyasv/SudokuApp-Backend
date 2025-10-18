from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from src.Models.TableModels import User
from src.Schemas.user_schema import UserData, User as baseUser

def get_user_data(user_id : UUID , db : Session) -> baseUser:
    user = db.query(User).filter(User.id == user_id).first()
    if(not user):
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "User not found")
    return user

