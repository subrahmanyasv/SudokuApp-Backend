from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    id: Optional[UUID]
    username: str
    email: EmailStr

class UserData(UserBase):
    total_games_played: int
    total_score: int
    best_score_easy: int
    best_score_medium: int
    best_score_hard: int

class User(UserData):
    id: Optional[UUID]
    username: str
    email: EmailStr

class UserResponse(BaseModel):
    status: str
    message: UserData


