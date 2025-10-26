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
    # *** CHANGE: Make solution_string optional in base ***
    solution_string: Optional[str] = None # Solution might not always be needed/present

    class Config:
        from_attributes = True


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
    current_state: Optional[str] = None # New field for current board state

    class Config:
        from_attributes = True

# *** ADDED: Unified History Response Schema ***
class GameHistoryItem(BaseModel):
    # Common Fields
    id: UUID # Game ID or Challenge ID
    difficulty: str
    duration_seconds: int # User's duration (if standard game or if user was participant)
    completed_at: Optional[datetime] = None
    puzzle: Optional[PuzzleBase] = None # Include basic puzzle info (no solution)
    # *** ADDED was_completed as Optional, default True for history ***
    was_completed: Optional[bool] = True

    # Standard Game Fields
    # *** CHANGED: Default to 0 instead of None to avoid int_type validation error ***
    final_score: Optional[int] = 0 # Only for standard games
    errors_made: Optional[int] = 0 # Only for standard games
    # *** ADDED hints_used as Optional, default 0 ***
    hints_used: Optional[int] = 0

    # Challenge Fields (Optional)
    is_challenge: bool = False
    challenger_id: Optional[UUID] = None
    opponent_id: Optional[UUID] = None
    challenger_username: Optional[str] = None
    opponent_username: Optional[str] = None
    winner_id: Optional[UUID] = None
    challenger_duration: Optional[int] = None
    opponent_duration: Optional[int] = None
    current_state: Optional[str] = None # Current board state if applicable


    class Config:
        from_attributes = True

# --- Update/Response Schemas ---
class UpdateResponse(BaseModel):
    message: str
    status: str

class GameResponseWithPuzzle(GameBase):
    puzzle: PuzzleBase # Include the full puzzle details
