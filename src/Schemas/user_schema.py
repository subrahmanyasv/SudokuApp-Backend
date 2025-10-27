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
    # *** ADDED: Challenge Stats ***
    total_challenges_played: int = 0
    total_challenges_won: int = 0

    class Config:
        from_attributes = True # Ensure this is present

class User(UserData):
    id: Optional[UUID]
    username: str
    email: EmailStr

class UserResponse(BaseModel):
    status: str
    message: UserData


