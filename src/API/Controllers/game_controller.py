from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, BackgroundTasks
from typing import List, Dict

from src.Security.security import validate_user
from src.Models.TableModels import Games, Puzzles, User
from src.Schemas.game_schema import GameBase, PuzzleBase, PuzzleCreate, GameCreate
from src.Schemas.auth_schema import TokenPayload
from src.Services.game_generator import generate_and_save_puzzles_background_task


def new_game(user: TokenPayload, db: Session, difficulty: str, background_tasks: BackgroundTasks) -> PuzzleBase:
    
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
        ).with_for_update().first()
        if not puzzle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No available puzzles of difficulty '{difficulty}'. Please try again later."
            )

        puzzle.is_used = True
        db.add(puzzle)

        new_game_instance = Games(user_id=user.id, puzzle_id=puzzle.id)
        db.add(new_game_instance)
        db.commit()
        db.refresh(puzzle)
        return puzzle

    except Exception as e:
        db.rollback()
        print(f"Error starting new game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {e}"
        )
    

def update_game(user: TokenPayload, db: Session, game_data: GameBase) -> bool:
    try:
        game_to_update = db.query(Games).filter(
            Games.id == game_data.id,
            Games.user_id == user.id
        ).first()

        if not game_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found or you do not have permission to update it."
            )

        game_to_update.was_completed = game_data.was_completed
        game_to_update.duration_seconds = game_data.duration_seconds
        game_to_update.errors_made = game_data.errors_made
        game_to_update.hints_used = game_data.hints_used
        game_to_update.final_score = game_data.final_score
        game_to_update.completed_at = game_data.completed_at

        db.add(game_to_update)

        user_stats = db.query(User).filter(User.id == user.id).with_for_update().first()
        if not user_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
        user_stats.total_games_played += 1
        user_stats.total_score += game_data.final_score

        if game_data.difficulty == "easy" and user_stats.best_score_easy < game_data.final_score:
            user_stats.best_score_easy = game_data.final_score
        elif game_data.difficulty == "medium" and user_stats.best_score_medium < game_data.final_score:
            user_stats.best_score_medium = game_data.final_score
        elif game_data.difficulty == "hard" and game_data.final_score > user_stats.best_score_hard:
            user_stats.best_score_hard = game_data.final_score
       
        db.add(user_stats)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error updating game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {e}"
        )
    

def get_games_count_util(db: Session) -> int:
        count = db.query(Puzzles).count()
        return count

def add_games_to_db_util(db: Session, games: List[Dict[str, str]] = [], difficulty: str = "easy"):
    
    for game in games:
        db.add(Puzzles(**game, difficulty=difficulty))
    db.commit()
    