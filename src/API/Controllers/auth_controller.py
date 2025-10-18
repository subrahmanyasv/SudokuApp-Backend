from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.Models.TableModels import User
from src.Schemas.auth_schema import AuthResponse, UserLogin, CreateUser
from src.Security.security import get_password_hash, verify_password, create_access_token

def create_user(newUser: CreateUser, db: Session) -> AuthResponse:
    existing_user = db.query(User).filter(User.email == newUser.email).first()
    
    if(existing_user):
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = "User already exists")
    
    print(newUser.password)
    hashed_password = get_password_hash(newUser.password)


    new_user = User(username = newUser.username, email = newUser.email, hashed_password = hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token({'email': newUser.email, 'username': newUser.username, "id": str(new_user.id)})

    message = f"username: {newUser.username}, email: {newUser.email}, user_id: {new_user.id}"

    return {
        "status": "success",
        "message": message,
        "token": access_token
    }


def login_user(user_credentials: UserLogin, db: Session) ->  AuthResponse:
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if(not user):
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "User not found")
    
    if(not verify_password(user_credentials.password, user.hashed_password)):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Incorrect password")
    
    access_token = create_access_token({'email': user_credentials.email, 'username': user.username, "id": str(user.id)})
    message = f"username: {user.username}, email: {user.email}, user_id: {user.id}"

    return {
        "status": "success",
        "message": message,
        "token": access_token
    }


