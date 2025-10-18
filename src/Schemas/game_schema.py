from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class PuzzleBase(BaseModel):
    id: Optional[UUID]
    difficulty: str
    board_string: str
    solution_string: str

class PuzzleCreate(BaseModel):
    difficulty: str
    board_string: str
    solution_string: str

class GameCreate(BaseModel):
    user_id: UUID
    puzzle_id: UUID

class GameBase(BaseModel):
    id: UUID
    difficulty: str
    was_completed: bool
    duration_seconds: int
    errors_made: int
    hints_used: int
    final_score: int
    completed_at: Optional[str]


class UpdateResponse(BaseModel):
    message: str
    status: str

