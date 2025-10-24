from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from src.Config.database import get_db_session
from src.Security.security import validate_user
from src.Schemas.auth_schema import TokenPayload
# Import your new controller and response model
from src.API.Controllers import leaderboard_controller
from src.Schemas.leaderboard_schema import LeaderboardResponse

router = APIRouter()

@router.get(
    "/",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get All Leaderboard Data"
)
def get_full_leaderboard_route(
    user: TokenPayload = Depends(validate_user), 
    db: Session = Depends(get_db_session)
):
    """
    Fetches all leaderboard data in one call.
    
    Returns a nested object containing:
    - **top_players**: Top 5 players for all 9 categories (3 difficulties x 3 timespans).
    - **user_ranks**: The requesting user's rank for all 9 categories.
    """
    try:
        # Call the new controller function
        data = leaderboard_controller.get_full_leaderboard(db, user)
        
        return LeaderboardResponse(
            status="success",
            message="Leaderboard data retrieved successfully",
            data=data
        )
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        # Let FastAPI handle the error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )