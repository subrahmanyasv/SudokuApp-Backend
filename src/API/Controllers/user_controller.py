# SudokuApp-Backend/src/API/Controllers/user_controller.py

from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional # Ensure List is imported

from src.Models.TableModels import User, Games, Puzzles # Ensure Games and Puzzles are imported
from src.Schemas.user_schema import UserData, UserResponse, UserBase
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

# *** MODIFIED: Return only Optional[GameResponseWithPuzzle] ***
def get_in_progress_game(db: Session, user: TokenPayload) -> Optional[GameResponseWithPuzzle]:
    """
    Retrieves the user's single most recent in-progress game.
    Returns the game details or None if no incomplete game exists.
    """
    # *** FIX: Query for the first game ordered by last_played descending ***
    in_progress_game = db.query(Games).join(Puzzles).filter(
        Games.user_id == user.id,
        Games.was_completed == False # Filter for incomplete games
    ).order_by(desc(Games.last_played)).first() # Get the most recent one

    if not in_progress_game:
        return None # Return None if no game is found

    # Construct the response object if a game is found
    puzzle_data = PuzzleBase(
        id=in_progress_game.puzzle.id,
        gameId=in_progress_game.id, # Include gameId
        difficulty=in_progress_game.puzzle.difficulty,
        board_string=in_progress_game.puzzle.board_string,
        solution_string=in_progress_game.puzzle.solution_string
    )
    game_data = GameResponseWithPuzzle(
        id=in_progress_game.id,
        difficulty=in_progress_game.puzzle.difficulty, # Get difficulty from puzzle
        was_completed=in_progress_game.was_completed,
        duration_seconds=in_progress_game.duration_seconds,
        errors_made=in_progress_game.errors_made,
        hints_used=in_progress_game.hints_used,
        final_score=in_progress_game.final_score,
        completed_at=in_progress_game.completed_at,
        current_state=in_progress_game.current_state,
        puzzle=puzzle_data
    )
    return game_data


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


def get_user_list(db: Session, user: TokenPayload) -> List[UserBase]:
    try:
        current_user_id = user.id
        all_other_users = db.query(User).filter(
            User.id != current_user_id
        ).order_by(User.username).all()
        user_list = [
            UserBase(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email
            )
            for db_user in all_other_users
        ]
        return user_list

    except Exception as e:
        print(f"Error getting user list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred while fetching the user list."
        )
