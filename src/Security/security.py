from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.Config.settings import settings
from src.Config.database import get_db_session
from src.Models.TableModels import User
from src.Schemas.auth_schema import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

http_bearer = HTTPBearer()



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_user(token: HTTPAuthorizationCredentials = Depends(http_bearer), db: Session = Depends(get_db_session)) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        user = db.query(User).get(token_data.id)
        if user is None:
            raise credentials_exception
        return token_data
    
    except JWTError:
        raise credentials_exception