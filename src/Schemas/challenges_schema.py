# src/Schemas/challenge_schema.py

from pydantic import BaseModel
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime

# =======================================================================
#  Input Schemas (Client to Server)
# =======================================================================

class ChallengeCreate(BaseModel):
    """
    Schema used when a challenger first creates a new challenge.
    This is sent after the challenger completes a game.
    """
    puzzle_id: UUID         # The ID of the puzzle the challenger just played
    opponent_id: UUID       # The ID of the user being challenged
    challenger_duration: int  # The challenger's final game time in seconds


class ChallengeRespond(BaseModel):
    """
    Schema used when an opponent accepts or rejects a challenge.
    """
    action: Literal["accept", "reject"]


class ChallengeComplete(BaseModel):
    """
    Schema used when an opponent submits their results for a completed challenge.
    """
    opponent_duration: int  # The opponent's final game time in seconds


# =======================================================================
#  Output Schemas (Server to Client)
# =======================================================================

class ChallengeUser(BaseModel):
    """Minimal user data for embedding in challenge responses."""
    id: UUID
    username: str

    class Config:
        from_attributes = True


class ChallengePuzzle(BaseModel):
    """
    Minimal puzzle data for embedding in challenge responses.
    Excludes the solution_string for fairness.
    """
    id: UUID
    difficulty: str
    board_string: str # The initial puzzle board
    solution_string: str # The solved puzzle board

    class Config:
        from_attributes = True


class ChallengeBase(BaseModel):
    """Base schema mapping directly to the Challenge model fields."""
    id: UUID
    puzzle_id: UUID
    challenger_id: UUID
    opponent_id: UUID
    status: str
    challenger_duration: int
    opponent_duration: Optional[int] = None
    winner_id: Optional[UUID] = None
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChallengeResponse(ChallengeBase):
    """
    Full challenge data for API responses, including nested objects
    for the puzzle, challenger, opponent, and winner.
    """
    puzzle: ChallengePuzzle
    challenger: ChallengeUser
    opponent: ChallengeUser
    winner: Optional[ChallengeUser] = None