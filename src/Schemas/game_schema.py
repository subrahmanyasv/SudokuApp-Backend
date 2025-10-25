from pydantic import BaseModel, EmailStr
from typing import Optional, Union # Added Union
from uuid import UUID
from datetime import datetime # Import datetime


# --- Puzzle Schemas ---
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

# --- Game Schemas ---
class GameCreate(BaseModel):
    user_id: UUID
    puzzle_id: UUID

class GameBase(BaseModel):
    id: UUID # This should be the Game ID
    difficulty: str # Added difficulty for easier access
    was_completed: bool
    duration_seconds: int
    errors_made: int
    hints_used: int
    final_score: int
    completed_at: Optional[Union[str, datetime]] = None

# New Schema: Game response including puzzle details
class GameResponseWithPuzzle(GameBase):
    puzzle: PuzzleBase # Include the full puzzle details

# --- Update/Response Schemas ---
class UpdateResponse(BaseModel):
    message: str
    status: str

