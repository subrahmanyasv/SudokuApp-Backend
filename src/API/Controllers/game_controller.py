from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from typing import List, Dict
import uuid # Ensure uuid is imported

from src.Security.security import validate_user
from src.Models.TableModels import Games, Puzzles, User
from src.Schemas.game_schema import GameBase, PuzzleBase, PuzzleCreate, GameCreate, UpdateResponse
from src.Schemas.auth_schema import TokenPayload


def new_game(user: TokenPayload, db: Session, difficulty: str) -> PuzzleBase:

    puzzle_count = db.query(Puzzles).filter(
        Puzzles.difficulty == difficulty,
        Puzzles.is_used == False
    ).count()

    if puzzle_count < 2:
        # TODO: Implement a background task to generate more puzzles.
        # This could be done using FastAPI's BackgroundTasks, Celery, etc.
        print(f"Low puzzle stock for difficulty '{difficulty}'. Triggering generation.")

    try:

        puzzle = db.query(Puzzles).filter(
            Puzzles.difficulty == difficulty,
            Puzzles.is_used == False
        ).with_for_update().first()
        if not puzzle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No available puzzles of difficulty '{difficulty}'. Please try again later."
            )

        puzzle.is_used = True
        db.add(puzzle)

        # Ensure user.id is correctly passed as UUID
        user_id_uuid = uuid.UUID(str(user.id)) if isinstance(user.id, str) else user.id

        new_game_instance = Games(user_id=user_id_uuid, puzzle_id=puzzle.id)
        db.add(new_game_instance)
        db.flush() # Use flush to get the ID before commit
        db.refresh(new_game_instance) # Refresh to get the generated ID

        db.commit() # Commit changes

        # Construct the response including the gameId
        puzzle_response = PuzzleBase(
            id=puzzle.id,
            gameId=new_game_instance.id, # Include the game ID here
            difficulty=puzzle.difficulty,
            board_string=puzzle.board_string,
            solution_string=puzzle.solution_string
        )
        return puzzle_response

    except Exception as e:
        db.rollback()
        print(f"Error starting new game: {e}")
        # Improve error detail logging if possible
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error occurred while starting a new game."
        )


def update_game(user: TokenPayload, db: Session, game_data: GameBase) -> bool:
    try:
        # Ensure user.id is correctly passed as UUID
        user_id_uuid = uuid.UUID(str(user.id)) if isinstance(user.id, str) else user.id
        game_id_uuid = uuid.UUID(str(game_data.id)) if isinstance(game_data.id, str) else game_data.id


        game_to_update = db.query(Games).filter(
            Games.id == game_id_uuid,
            Games.user_id == user_id_uuid
        ).with_for_update().first() # Use with_for_update for locking

        if not game_to_update:
            print(f"Game not found for update: game_id={game_id_uuid}, user_id={user_id_uuid}") # Log IDs
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found or you do not have permission to update it."
            )

        # Only update specific fields
        game_to_update.was_completed = game_data.was_completed
        game_to_update.duration_seconds = game_data.duration_seconds
        game_to_update.errors_made = game_data.errors_made
        game_to_update.hints_used = game_data.hints_used # Keep track even if 0 now
        game_to_update.final_score = game_data.final_score
        # game_to_update.completed_at = game_data.completed_at # Let DB handle timestamp or set based on was_completed

        # Update user stats only if game was completed successfully
        if game_data.was_completed:
            user_stats = db.query(User).filter(User.id == user_id_uuid).with_for_update().first()
            if not user_stats:
                # This case should ideally not happen if the user exists
                 db.rollback() # Rollback game update if user not found
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found for stats update.")

            user_stats.total_games_played += 1
            user_stats.total_score += game_data.final_score

            # Update best scores based on difficulty
            if game_data.difficulty == "easy" and game_data.final_score > user_stats.best_score_easy:
                user_stats.best_score_easy = game_data.final_score
            elif game_data.difficulty == "medium" and game_data.final_score > user_stats.best_score_medium:
                user_stats.best_score_medium = game_data.final_score
            elif game_data.difficulty == "hard" and game_data.final_score > user_stats.best_score_hard:
                user_stats.best_score_hard = game_data.final_score
            # No need to explicitly add user_stats, SQLAlchemy tracks changes

        db.commit() # Commit transaction
        return True

    except HTTPException as http_exc:
        db.rollback() # Rollback on known HTTP errors
        raise http_exc # Re-raise the exception
    except Exception as e:
        db.rollback() # Rollback on any other errors
        print(f"Unexpected error updating game: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred during game update."
        )


def get_games_count_util(db: Session) -> int:
        count = db.query(Puzzles).count()
        return count

def add_games_to_db_util(db: Session, games: List[Dict[str, str]] = [], difficulty: str = "easy"):

    for game in games:
        db.add(Puzzles(**game, difficulty=difficulty))
    db.commit()
