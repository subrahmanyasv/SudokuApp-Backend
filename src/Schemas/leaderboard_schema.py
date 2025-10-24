from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID

class LeaderboardEntry(BaseModel):
    """Defines a single entry in a Top 5 list."""
    user_id: UUID
    username: str
    total_score: int
    rank: int

    class Config:
        from_attributes = True  # Allows pydantic to read from SQLAlchemy models

class UserRankEntry(BaseModel):
    """Defines the user's specific rank for a category."""
    total_score: int
    rank: int
    
    class Config:
        from_attributes = True

# --- Nested data structures for the response ---

class LeaderboardCategoryData(BaseModel):
    """Holds the Top 5 lists for one difficulty."""
    daily: List[LeaderboardEntry]
    weekly: List[LeaderboardEntry]
    all_time: List[LeaderboardEntry]

class UserRankCategoryData(BaseModel):
    """Holds the user's ranks for one difficulty."""
    daily: Optional[UserRankEntry] = None
    weekly: Optional[UserRankEntry] = None
    all_time: Optional[UserRankEntry] = None

class FullLeaderboardData(BaseModel):
    """The main 'data' object in the response."""
    top_players: Dict[str, LeaderboardCategoryData]  # Keys: "easy", "medium", "hard"
    user_ranks: Dict[str, UserRankCategoryData]    # Keys: "easy", "medium", "hard"

class LeaderboardResponse(BaseModel):
    """The final, top-level API response model."""
    status: str
    message: str
    data: FullLeaderboardData