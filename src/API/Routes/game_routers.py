from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.Security.security import validate_user
from src.Config.database import get_db_session
from src.API.Controllers import game_controller
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.game_schema import GameCreate, GameBase, PuzzleBase, PuzzleCreate, UpdateResponse


router = APIRouter()

@router.get("/new_game/{difficulty}",
    response_model=PuzzleBase,
    status_code=status.HTTP_200_OK)
def new_game(background_tasks: BackgroundTasks, user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session), difficulty: str = "easy"):
    try:
        return game_controller.new_game(user, db, difficulty, background_tasks)
    except Exception as e:
        print(f"Error creating new game: {e}")
        return {"status": "error", "message": f"Error creating new game: {e}"}


@router.put("/update_game",
    response_model= UpdateResponse,
    status_code=status.HTTP_200_OK)
def update_game(user: TokenPayload = Depends(validate_user), db: Session = Depends(get_db_session), game_data: GameBase = None):
    try:
        game_controller.update_game(user, db, game_data)
        return {"status": "success", "message": "Game updated successfully"}
    except Exception as e:
        print(f"Error updating game: {e}")
        return {"status": "error", "message": f"Error updating game: {e}"}