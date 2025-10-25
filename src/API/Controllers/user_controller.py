from typing import Optional
from sqlalchemy.orm import Session, joinedload # Import joinedload
from fastapi import HTTPException, status
from uuid import UUID
from sqlalchemy import desc # Import desc for ordering

# Import necessary models and schemas
from src.Models.TableModels import User, Games, Puzzles
from src.Schemas.user_schema import UserData, User as BaseUser
from src.Schemas.game_schema import GameResponseWithPuzzle, PuzzleBase # Import new schemas


def get_user_data(user_id : UUID , db : Session) -> BaseUser:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "User not found")
    # Manually construct the BaseUser object if needed, or ensure User model matches
    # Assuming User model has all necessary fields defined in BaseUser schema
    return BaseUser.model_validate(user, from_attributes=True)


def get_in_progress_game(user_id: UUID, db: Session) -> Optional[GameResponseWithPuzzle]:
    """
    Finds the most recent game for the user that was not completed.
    Includes puzzle details using joined loading.
    """
    latest_unfinished_game = (
        db.query(Games)
        .options(joinedload(Games.puzzle))  # Eager load the related puzzle
        .filter(Games.user_id == user_id, Games.was_completed == False)
        .order_by(desc(Games.completed_at), desc(Games.id))  # Order by completion attempt then creation
        .first()
    )

    if not latest_unfinished_game:
        return None

    # Adapt the Puzzle model instance to PuzzleBase schema
    puzzle_data = PuzzleBase(
        id=latest_unfinished_game.puzzle.id,
        gameId=latest_unfinished_game.id, # Pass the game ID back
        difficulty=latest_unfinished_game.puzzle.difficulty,
        board_string=latest_unfinished_game.puzzle.board_string,
        solution_string=latest_unfinished_game.puzzle.solution_string
    )

    # Adapt the Game model instance (with loaded puzzle) to GameResponseWithPuzzle
    game_response = GameResponseWithPuzzle(
        id=latest_unfinished_game.id,
        difficulty=latest_unfinished_game.puzzle.difficulty, # Get difficulty from puzzle
        was_completed=latest_unfinished_game.was_completed,
        duration_seconds=latest_unfinished_game.duration_seconds,
        errors_made=latest_unfinished_game.errors_made,
        hints_used=latest_unfinished_game.hints_used,
        final_score=latest_unfinished_game.final_score,
        completed_at=latest_unfinished_game.completed_at, # This will be None/null
        puzzle=puzzle_data # Assign the adapted puzzle data
    )

    return game_response
