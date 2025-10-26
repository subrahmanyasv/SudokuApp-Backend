# SudokuApp-Backend/src/API/Routes/user_routes.py

from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException # Import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID # Import UUID

from src.Config.database import get_db_session
from src.Schemas.game_schema import GameResponseWithPuzzle # This now includes current_state
from src.Security.security import validate_user
from src.Schemas.user_schema import UserData, User as baseUser, UserResponse
from src.Schemas.auth_schema import TokenPayload
from src.API.Controllers import user_controller

router = APIRouter()

@router.get("/",
    response_model = UserResponse,
    status_code=status.HTTP_200_OK)
def get_user(user : TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session)):
    try:
        user_data = user_controller.get_user_data(db,user) # Ensure ID is UUID
        response = UserResponse(
            status="success",
            message=user_data # Directly assign the validated user data
        )
        return response
    except HTTPException as http_exc:
        # Re-raise known exceptions from controller
        raise http_exc
    except Exception as e:
        print(f"Error getting user data in router: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/in_progress_game",
    # *** FIX: Ensure response_model includes the updated GameResponseWithPuzzle ***
    response_model=Optional[GameResponseWithPuzzle],
    status_code=status.HTTP_200_OK,
    summary="Get the user's most recent unfinished game")
def get_in_progress_game_route(user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session)):
    """
    Fetches the latest game started by the authenticated user that is marked as incomplete.
    Returns the game details including the associated puzzle and current board state,
    or null if no incomplete game exists.
    """
    try:
        game_data = user_controller.get_in_progress_game(UUID(str(user.id)), db) # Ensure ID is UUID
        return game_data # Will return the game object or None
    except HTTPException as http_exc:
        # Re-raise known exceptions
        raise http_exc
    except Exception as e:
        print(f"Error fetching in-progress game in router: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- NEW ROUTE for Game History ---
@router.get(
    "/game_history",
    response_model=List[GameResponseWithPuzzle], # Response is a list of completed games
    status_code=status.HTTP_200_OK,
    summary="Get User's Game History"
)
def get_game_history_route(
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches the completed game history for the authenticated user,
    ordered by completion date (most recent first).
    """
    try:
        game_history_list = user_controller.get_game_history(db, user)
        return game_history_list # Directly return the list
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error getting game history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch game history."
        )