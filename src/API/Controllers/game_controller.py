# SudokuApp-Backend/src/API/Controllers/game_controller.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, BackgroundTasks
from typing import List, Dict
import uuid
import datetime # Import datetime

from src.Config.database import get_db_session # Correct import
from src.Security.security import validate_user
from src.Models.TableModels import Games, Puzzles, User
from src.Schemas.game_schema import GameBase, PuzzleBase, PuzzleCreate, GameCreate, UpdateResponse # Correct schemas from your file
from src.Schemas.auth_schema import TokenPayload
from src.Services.game_generator import generate_and_save_puzzles_background_task
# leaderboard_services import is not needed here based on your uploaded controller file

def new_game(user: TokenPayload, db: Session, difficulty: str, background_tasks: BackgroundTasks) -> PuzzleBase:
    """
    Finds an unused puzzle, marks it used, creates a game record,
    and triggers background generation if needed.
    Returns puzzle details including the new game ID.
    """
    
    # *** CHANGE: This check is REMOVED to allow multiple in-progress games. ***
    # existing_game = db.query(Games).filter(
    #     Games.user_id == user_id_uuid,
    #     Games.was_completed == False
    # ).first()
    # if existing_game:
    #     raise HTTPException(status_code=400, detail="User already has an ongoing game. Complete or delete it first.")

    puzzle_count = db.query(Puzzles).filter(
        Puzzles.difficulty == difficulty,
        Puzzles.is_used == False
    ).count()

    if puzzle_count < 2:
        background_tasks.add_task(generate_and_save_puzzles_background_task, difficulty)

    try:
        puzzle = db.query(Puzzles).filter(
            Puzzles.difficulty == difficulty,
            Puzzles.is_used == False
        ).with_for_update().first() # Lock the row

        if not puzzle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No available puzzles of difficulty '{difficulty}'. Please try again later."
            )

        puzzle.is_used = True
        db.add(puzzle)

        user_id_uuid = uuid.UUID(str(user.id)) if isinstance(user.id, str) else user.id

        # *** FIX: Set initial current_state to the puzzle board string ***
        new_game_instance = Games(
            user_id=user_id_uuid,
            puzzle_id=puzzle.id,
            current_state=puzzle.board_string # Initialize with puzzle board
        )
        db.add(new_game_instance)
        db.flush() # Get the new game ID before commit
        db.refresh(new_game_instance)

        db.commit()

        puzzle_response = PuzzleBase(
            id=puzzle.id,
            gameId=new_game_instance.id, # Include game ID
            difficulty=puzzle.difficulty,
            board_string=puzzle.board_string,
            solution_string=puzzle.solution_string
        )
        return puzzle_response

    except Exception as e:
        db.rollback()
        print(f"Error starting new game: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error occurred while starting a new game."
        )


def update_game(user: TokenPayload, db: Session, game_data: GameBase) -> UpdateResponse:
    """
    Updates an existing game record based on the provided GameBase data.
    Handles completion status, updates user stats if completed, and saves current board state.
    Returns an UpdateResponse object.
    """
    try:
        user_id_uuid = uuid.UUID(str(user.id)) if isinstance(user.id, str) else user.id
        game_id_uuid = uuid.UUID(str(game_data.id)) if isinstance(game_data.id, str) else game_data.id

        # *** FIX: Removed .with_for_update() to simplify the transaction ***
        game_to_update = db.query(Games).filter(
            Games.id == game_id_uuid,
            Games.user_id == user_id_uuid
        ).first()

        if not game_to_update:
            print(f"Game not found for update: game_id={game_id_uuid}, user_id={user_id_uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found or you do not have permission to update it."
            )

        # *** FIX: Add server-side logging ***
        print(f"--- PRE-UPDATE (Game ID: {game_id_uuid}) ---")
        print(f"DB duration_seconds: {game_to_update.duration_seconds}")
        print(f"DB current_state: {game_to_update.current_state}")
        print(f"INCOMING duration_seconds: {game_data.duration_seconds}")
        print(f"INCOMING current_state: {game_data.current_state}")
        # --- End Logging ---


        # *** FIX: Save the current board state if provided ***
        if game_data.current_state and len(game_data.current_state) == 81:
            game_to_update.current_state = game_data.current_state
        elif not game_data.was_completed:
            # If not completed and no state sent, maybe log a warning?
            print(f"Warning: Game update for game {game_id_uuid} received without current_state.")


        # Update other fields from GameBase
        game_to_update.was_completed = game_data.was_completed
        game_to_update.duration_seconds = game_data.duration_seconds
        game_to_update.errors_made = game_data.errors_made
        game_to_update.hints_used = game_data.hints_used # Keep track even if 0
        game_to_update.final_score = game_data.final_score
        game_to_update.last_played = datetime.datetime.utcnow() # Update last played timestamp


        if game_data.was_completed:
            game_to_update.completed_at = game_data.completed_at or datetime.datetime.utcnow() # Use provided or now

            # *** FIX: Removed .with_for_update() here as well ***
            user_stats = db.query(User).filter(User.id == user_id_uuid).first()
            if not user_stats:
                 db.rollback()
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found for stats update.")

            # Ensure stats fields are not None before incrementing
            user_stats.total_games_played = (user_stats.total_games_played or 0) + 1
            user_stats.total_score = (user_stats.total_score or 0) + game_data.final_score

            if game_data.difficulty == "easy":
                 current_best = user_stats.best_score_easy or 0
                 if game_data.final_score > current_best:
                      user_stats.best_score_easy = game_data.final_score
            elif game_data.difficulty == "medium":
                 current_best = user_stats.best_score_medium or 0
                 if game_data.final_score > current_best:
                      user_stats.best_score_medium = game_data.final_score
            elif game_data.difficulty == "hard":
                 current_best = user_stats.best_score_hard or 0
                 if game_data.final_score > current_best:
                      user_stats.best_score_hard = game_data.final_score
            
            # *** FIX: Explicitly add user_stats to session if needed ***
            db.add(user_stats)

        # *** FIX: Explicitly add game_to_update to the session before commit ***
        # This tells SQLAlchemy the object is "dirty" and needs to be saved.
        db.add(game_to_update)
        
        # *** FIX: Add server-side logging ***
        print(f"--- POST-UPDATE (Game ID: {game_id_uuid}) ---")
        print(f"SAVING duration_seconds: {game_to_update.duration_seconds}")
        print(f"SAVING current_state: {game_to_update.current_state}")
        # --- End Logging ---

        db.commit()
        print("--- COMMIT SUCCESSFUL ---")
        return UpdateResponse(status="success", message="Game updated successfully") # Return UpdateResponse

    except HTTPException as http_exc:
        db.rollback()
        print(f"--- HTTP EXCEPTION (ROLLBACK) ---: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"--- UNEXPECTED ERROR (ROLLBACK) ---: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred during game update."
        )