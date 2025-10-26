# SudokuApp-Backend/src/API/Routes/game_routers.py

from http.client import HTTPException
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.Security.security import validate_user
from src.Config.database import get_db_session
from src.API.Controllers import game_controller
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.game_schema import GameCreate, GameBase, PuzzleBase, PuzzleCreate, UpdateResponse # GameBase includes current_state now


router = APIRouter()

@router.get("/new_game/{difficulty}",
    response_model=PuzzleBase,
    status_code=status.HTTP_200_OK)
def new_game(background_tasks: BackgroundTasks, user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session), difficulty: str = "easy"):
    try:
        return game_controller.new_game(user, db, difficulty, background_tasks)
    except Exception as e:
        print(f"Error creating new game: {e}")
        # Consider re-raising HTTPException for better error handling in FastAPI
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/update_game",
    response_model= UpdateResponse,
    status_code=status.HTTP_200_OK)
# *** FIX: Ensure game_data uses GameBase schema which now includes optional current_state ***
def update_game(user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session), game_data: GameBase = None):
    # Basic check if game_data is provided
    if game_data is None:
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Request body cannot be empty.")

    try:
        # Controller now returns UpdateResponse directly on success
        return game_controller.update_game(user, db, game_data)
    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions from the controller
        raise http_exc
    except Exception as e:
        print(f"Error updating game in router: {e}")
        # Re-raise other exceptions as internal server errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
