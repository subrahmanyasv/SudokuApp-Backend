# SudokuApp-Backend/src/API/Routes/user_routes.py

from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from src.Config.database import get_db_session
# *** CORRECTED IMPORT: Use GameHistoryItem for history and in-progress ***
from src.Schemas.game_schema import GameHistoryItem, GameResponseWithPuzzle # Keep GameResponseWithPuzzle if used elsewhere, maybe in-progress?
from src.Security.security import validate_user
# *** CORRECTED IMPORT: Import UserBase directly ***
from src.Schemas.user_schema import UserData, UserResponse, UserBase # Removed 'User as baseUser'
from src.Schemas.auth_schema import TokenPayload
from src.API.Controllers import user_controller

router = APIRouter()

@router.get(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile" # Added summary
)
def get_user(user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session)):
    """
    Fetches the profile data for the currently authenticated user,
    including username, email, and game statistics.
    """
    try:
        user_data = user_controller.get_user_data(db, user)
        response = UserResponse(
            status="success",
            message=user_data
        )
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error getting user data in router: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/in_progress_game",
    # *** CORRECTED: Use the unified history schema, but response can be null ***
    response_model=Optional[GameHistoryItem], # Was Optional[GameResponseWithPuzzle]
    status_code=status.HTTP_200_OK,
    summary="Get User's Most Recent In-Progress Standard Game" # Updated summary
)
def get_in_progress_game_route(
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches the user's most recently saved *standard* game that is not yet completed.
    Returns the game details including the associated puzzle (with solution string)
    and current board state, formatted as a GameHistoryItem, or null if none exists.
    Challenges are not included here.
    """
    try:
        # Controller now returns GameHistoryItem or None
        game_data = user_controller.get_in_progress_game(db, user)
        return game_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error fetching in-progress game in router: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# --- ROUTE for Game History ---
@router.get(
    "/game_history",
    # *** CORRECTED: Use the new unified history schema ***
    response_model=List[GameHistoryItem], # Was List[GameResponseWithPuzzle]
    status_code=status.HTTP_200_OK,
    summary="Get User's Combined Game and Challenge History" # Updated summary
)
def get_game_history_route(
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches the completed game history for the authenticated user,
    including both standard games and challenges they participated in,
    ordered by completion date (most recent first).
    """
    try:
        # Controller now returns List[GameHistoryItem]
        game_history_list = user_controller.get_game_history(db, user)
        return game_history_list
    except HTTPException as e:
        raise e # Re-raise known HTTP errors
    except Exception as e:
        print(f"Error fetching game history in router: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for easier debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch game history."
        )


@router.get(
    "/user_list",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
    summary="Get List of Other Users (with optional search)" # Updated summary
)
def get_user_list(
    # *** ADDED: Optional query parameter 'username' ***
    username: Optional[str] = Query(None, description="Optional search term for username (case-insensitive)"),
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches a list of all registered users except the currently authenticated one,
    ordered by username. Includes user ID, username, and email.

    Optionally filters the list based on the provided `username` query parameter
    (case-insensitive partial match).
    """
    try:
        # *** Pass the username search term to the controller ***
        return user_controller.get_user_list(db, user, username)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error getting user list in router: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))