from sqlalchemy.orm import Session
from src.Models.TableModels import Leaderboard
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.leaderboard_schema import (
    FullLeaderboardData, 
    LeaderboardCategoryData, 
    UserRankCategoryData
)

def get_full_leaderboard(db: Session, user: TokenPayload) -> FullLeaderboardData:
    
    difficulties = ["easy", "medium", "hard"]
    timespans = ["daily", "weekly", "all_time"]
    
    # --- 1. Efficiently query all Top 5 players at once ---
    top_5_query = db.query(Leaderboard).filter(
        Leaderboard.difficulty.in_(difficulties),
        Leaderboard.timespan.in_(timespans),
        Leaderboard.rank <= 5
    ).order_by(Leaderboard.rank).all()
    
    # Initialize a nested dictionary for top players
    top_players_data = {
        diff: {"daily": [], "weekly": [], "all_time": []} for diff in difficulties
    }
    
    # Sort the query results into the dictionary
    for entry in top_5_query:
        if entry.difficulty in top_players_data and entry.timespan in top_players_data[entry.difficulty]:
            top_players_data[entry.difficulty][entry.timespan].append(entry)

    # --- 2. Efficiently query all of the user's ranks at once ---
    user_ranks_query = db.query(Leaderboard).filter(
        Leaderboard.difficulty.in_(difficulties),
        Leaderboard.timespan.in_(timespans),
        Leaderboard.user_id == user.id
    ).all()

    # Initialize a nested dictionary for user ranks
    user_ranks_data = {
        diff: {"daily": None, "weekly": None, "all_time": None} for diff in difficulties
    }
    
    # Sort the query results into the dictionary
    for entry in user_ranks_query:
        if entry.difficulty in user_ranks_data and entry.timespan in user_ranks_data[entry.difficulty]:
            user_ranks_data[entry.difficulty][entry.timespan] = entry

    # --- 3. Format the data into Pydantic models for a clean response ---
    
    # This step ensures the data is correctly shaped and validated by Pydantic
    formatted_top_players = {
        diff: LeaderboardCategoryData(**categories) 
        for diff, categories in top_players_data.items()
    }
            
    formatted_user_ranks = {
        diff: UserRankCategoryData(**categories) 
        for diff, categories in user_ranks_data.items()
    }

    # Return the final, combined data object
    return FullLeaderboardData(
        top_players=formatted_top_players,
        user_ranks=formatted_user_ranks
    )