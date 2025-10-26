from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str



class AuthResponse(BaseModel):
    status: str
    message: str
    token: Optional[str]
    userId: Optional[str] # Changed from UUID to str to match token payload and ease frontend use


class TokenPayload(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    id: Optional[UUID]