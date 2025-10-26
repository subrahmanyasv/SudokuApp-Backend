# SudokuApp-Backend/src/API/Controllers/user_controller.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional # Ensure List is imported

from src.Models.TableModels import User, Games, Puzzles # Ensure Games and Puzzles are imported
from src.Schemas.user_schema import UserData, UserResponse
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.game_schema import GameResponseWithPuzzle, PuzzleBase # Import necessary game schemas

def get_user_data(db: Session, user: TokenPayload) -> UserData:
    """
    Retrieves user profile data including game statistics.
    """
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserData(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        total_games_played=db_user.total_games_played,
        total_score=db_user.total_score,
        best_score_easy=db_user.best_score_easy,
        best_score_medium=db_user.best_score_medium,
        best_score_hard=db_user.best_score_hard,
    )

def get_in_progress_game(db: Session, user: TokenPayload) -> List[GameResponseWithPuzzle]:
    """
    Retrieves the user's currently in-progress games (not completed).
    Returns a list of games.
    """
    in_progress_games = db.query(Games).join(Puzzles).filter(
        Games.user_id == user.id,
        Games.was_completed == False # Filter for incomplete games
    ).order_by(Games.last_played.desc()).all() # Fetch all matching games

    games_response_list = []
    if in_progress_games:
        for game in in_progress_games:
            puzzle_data = PuzzleBase(
                id=game.puzzle.id,
                gameId=game.id, # Link back to the game ID
                difficulty=game.puzzle.difficulty,
                board_string=game.puzzle.board_string,
                solution_string=game.puzzle.solution_string
            )
            game_data = GameResponseWithPuzzle(
                id=game.id,
                difficulty=game.puzzle.difficulty, # Include difficulty directly
                was_completed=game.was_completed,
                duration_seconds=game.duration_seconds,
                errors_made=game.errors_made,
                hints_used=game.hints_used,
                final_score=game.final_score,
                completed_at=game.completed_at,
                current_state=game.current_state, # Include current state
                puzzle=puzzle_data
            )
            games_response_list.append(game_data)

    return games_response_list


# --- NEW FUNCTION for Game History ---
def get_game_history(db: Session, user: TokenPayload) -> List[GameResponseWithPuzzle]:
    """
    Retrieves the user's completed game history.
    Returns a list of completed games, ordered by completion date descending.
    """
    completed_games = db.query(Games).join(Puzzles).filter(
        Games.user_id == user.id,
        Games.was_completed == True # Filter for completed games
    ).order_by(Games.completed_at.desc()).all() # Order by most recently completed

    history_list = []
    if completed_games:
        for game in completed_games:
            puzzle_data = PuzzleBase(
                id=game.puzzle.id,
                gameId=game.id,
                difficulty=game.puzzle.difficulty,
                board_string=game.puzzle.board_string,
                solution_string=game.puzzle.solution_string
            )
            game_data = GameResponseWithPuzzle(
                id=game.id,
                difficulty=game.puzzle.difficulty,
                was_completed=game.was_completed,
                duration_seconds=game.duration_seconds,
                errors_made=game.errors_made,
                hints_used=game.hints_used,
                final_score=game.final_score,
                completed_at=game.completed_at,
                current_state=game.current_state, # Can be null or solution string for completed
                puzzle=puzzle_data
            )
            history_list.append(game_data)

    return history_list