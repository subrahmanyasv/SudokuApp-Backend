from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.Config.database import get_db_session
from src.Schemas.game_schema import GameResponseWithPuzzle
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
        user =  user_controller.get_user_data(user.id, db)
        response = {
            "status": "success",
            "message": user
        }

        return response
    except Exception as e:
        print(f"Error getting user: {e}")
        return {"status": "error", "message": f"Error getting user: {e}"}

@router.get("/in_progress_game",
    response_model=Optional[GameResponseWithPuzzle], # Response can be a game or null
    status_code=status.HTTP_200_OK,
    summary="Get the user's most recent unfinished game")
def get_in_progress_game_route(user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session)):
    """
    Fetches the latest game started by the authenticated user that is marked as incomplete.
    Returns the game details along with the associated puzzle, or null if no incomplete game exists.
    """
    try:
        game_data = user_controller.get_in_progress_game(user.id, db)
        return game_data # Will return the game object or None (FastAPI handles Optional[None] as null)
    except Exception as e:
        print(f"Error fetching in-progress game: {e}")
       
