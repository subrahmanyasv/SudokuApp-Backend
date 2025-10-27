# Relative Path: user_controller.py

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from src.Models.TableModels import User, Games, Puzzles, Challenges
from src.Schemas.user_schema import UserData, UserResponse, UserBase
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.game_schema import GameHistoryItem, PuzzleBase

def get_user_data(db: Session, user: TokenPayload) -> UserData:
    """
    Retrieves user profile data including game statistics and challenge statistics.
    """
    user_id = user.id # Get UUID directly
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # *** ADDED: Calculate Challenge Stats ***
    total_challenges_played = db.query(Challenges).filter(
        Challenges.status == "completed",
        or_(Challenges.challenger_id == user_id, Challenges.opponent_id == user_id)
    ).count()

    total_challenges_won = db.query(Challenges).filter(
        Challenges.status == "completed",
        Challenges.winner_id == user_id
    ).count()
    # *** END: Calculate Challenge Stats ***

    # Use 0 as fallback for nullable integer fields
    return UserData(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        total_games_played=db_user.total_games_played or 0,
        total_score=db_user.total_score or 0,
        best_score_easy=db_user.best_score_easy or 0,
        best_score_medium=db_user.best_score_medium or 0,
        best_score_hard=db_user.best_score_hard or 0,
        # *** ADDED: Pass Challenge Stats to Schema ***
        total_challenges_played=total_challenges_played,
        total_challenges_won=total_challenges_won
    )



def get_in_progress_game(db: Session, user: TokenPayload) -> Optional[GameHistoryItem]:
    """
    Retrieves the user's most recent in-progress standard game.
    """
    user_id_uuid = user.id
    in_progress_game = db.query(Games).join(Puzzles).filter(
        Games.user_id == user.id,
        Games.was_completed == False
    ).order_by(desc(Games.last_played)).options(joinedload(Games.puzzle)).first()

    if not in_progress_game or not in_progress_game.puzzle:
        return None

    # *** Logging fetched data ***
    print(f"--- FETCHED In-Progress Game (ID: {in_progress_game.id}) ---")
    print(f"DB duration_seconds: {in_progress_game.duration_seconds}")
    print(f"DB errors_made: {in_progress_game.errors_made}") # Log fetched errors
    print(f"DB current_state: {in_progress_game.current_state}") # Log fetched state
    # --- End Logging ---

    puzzle_data = PuzzleBase(
        id=in_progress_game.puzzle.id,
        gameId=in_progress_game.id,
        difficulty=in_progress_game.puzzle.difficulty,
        board_string=in_progress_game.puzzle.board_string,
        solution_string=in_progress_game.puzzle.solution_string # Include solution for standard games
    )

    # *** FIX: Map all relevant fields including current_state ***
    return GameHistoryItem(
        id=in_progress_game.id,
        difficulty=in_progress_game.puzzle.difficulty,
        duration_seconds=in_progress_game.duration_seconds or 0, # Use fetched value or 0
        completed_at=None, # In-progress games don't have this
        puzzle=puzzle_data,
        final_score=0, # Not applicable for in-progress
        errors_made=in_progress_game.errors_made or 0, # Use fetched value or 0
        hints_used=in_progress_game.hints_used or 0,   # Use fetched value or 0
        is_challenge=False,
        was_completed=False, # Explicitly false
        current_state=in_progress_game.current_state # *** ADDED THIS LINE ***
    )


def get_game_history(db: Session, user: TokenPayload) -> List[GameHistoryItem]:
    """
    Retrieves the user's completed standard games AND completed challenges
    where the user was a participant.
    Returns a list of unified history items, ordered by completion date descending.
    """
    history_items = []
    user_id_uuid = user.id

    # 1. Fetch Completed Standard Games
    completed_games = db.query(Games).join(Puzzles).filter(
        Games.user_id == user_id_uuid,
        Games.was_completed == True
    ).options(joinedload(Games.puzzle)).order_by(Games.completed_at.desc()).all()

    for game in completed_games:
        puzzle_data = None
        if game.puzzle:
            puzzle_data = PuzzleBase(
                 id=game.puzzle.id,
                 gameId=game.id,
                 difficulty=game.puzzle.difficulty,
                 board_string=game.puzzle.board_string
            )

        history_items.append(GameHistoryItem(
            id=game.id,
            difficulty=game.puzzle.difficulty if game.puzzle else "unknown",
            duration_seconds=game.duration_seconds or 0,
            completed_at=game.completed_at,
            puzzle=puzzle_data,
            # *** Ensure standard game fields have defaults if potentially null from DB ***
            final_score=game.final_score or 0,
            errors_made=game.errors_made or 0,
            hints_used=game.hints_used or 0, # Pass hints_used
            was_completed=game.was_completed, # Pass was_completed
            is_challenge=False
        ))

    # 2. Fetch Completed Challenges involving the user
    completed_challenges = db.query(Challenges).filter(
        Challenges.status == 'completed',
        or_(
            Challenges.challenger_id == user_id_uuid,
            Challenges.opponent_id == user_id_uuid
        )
    ).options(
        joinedload(Challenges.puzzle),
        joinedload(Challenges.challenger),
        joinedload(Challenges.opponent),
        joinedload(Challenges.winner)
    ).order_by(Challenges.completed_at.desc()).all()

    for challenge in completed_challenges:
        puzzle_data = None
        if challenge.puzzle:
             puzzle_data = PuzzleBase(
                 id=challenge.puzzle.id,
                 gameId=game.id,
                 difficulty=challenge.puzzle.difficulty,
                 board_string=challenge.puzzle.board_string
             )

        user_duration = 0
        if user_id_uuid == challenge.challenger_id:
            user_duration = challenge.challenger_duration or 0
        elif user_id_uuid == challenge.opponent_id:
            user_duration = challenge.opponent_duration or 0

        history_items.append(GameHistoryItem(
            id=challenge.id,
            difficulty=challenge.puzzle.difficulty if challenge.puzzle else "unknown",
            duration_seconds=user_duration,
            completed_at=challenge.completed_at,
            puzzle=puzzle_data,
            # Standard game fields default to 0/False in schema for challenges
            # Challenge fields
            is_challenge=True,
            challenger_id=challenge.challenger_id,
            opponent_id=challenge.opponent_id,
            challenger_username=challenge.challenger.username if challenge.challenger else "Unknown",
            opponent_username=challenge.opponent.username if challenge.opponent else "Unknown",
            winner_id=challenge.winner_id,
            challenger_duration=challenge.challenger_duration,
            opponent_duration=challenge.opponent_duration,
            # *** Explicitly pass was_completed=True for completed challenges ***
            was_completed=True
            # hints_used will default to 0
        ))

    # 3. Sort Combined List by Completion Date (most recent first)
    history_items.sort(key=lambda item: item.completed_at if item.completed_at else datetime.min, reverse=True)

    return history_items


def get_user_list(db: Session, user: TokenPayload, username_search: Optional[str] = None) -> List[UserBase]:
    """
    Retrieves a list of all users except the currently authenticated one.
    Optionally filters by username (case-insensitive partial match).
    """
    try:
        current_user_id = user.id
        query = db.query(User).filter(User.id != current_user_id)

        # *** ADDED: Apply filter if username_search is provided ***
        if username_search:
            # Use ilike for case-insensitive partial matching
            query = query.filter(User.username.ilike(f"%{username_search}%"))

        # Order and execute the query
        all_other_users = query.order_by(User.username).all()

        user_list = [
            UserBase(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email # Consider if email should be excluded for privacy
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

