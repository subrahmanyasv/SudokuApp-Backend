from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class PuzzleBase(BaseModel):
    id: Optional[UUID] # This is the Puzzle ID
    gameId: Optional[UUID] # Add this field for the associated Game ID
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
    id: UUID # This should be the Game ID
    difficulty: str
    was_completed: bool
    duration_seconds: int
    errors_made: int
    hints_used: int
    final_score: int
    completed_at: Optional[str] # Keep as string for now for simplicity


class UpdateResponse(BaseModel):
    message: str
    status: str
