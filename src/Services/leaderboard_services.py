# src/Services/leaderboard_service.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time
from src.Config.database import getSessionLocal
from src.Models.TableModels import Leaderboard, User, Games, Puzzles

def get_db_session_for_job():
    """Creates a new, independent DB session for background jobs."""
    SessionLocal = getSessionLocal()
    if not SessionLocal:
        print("Error: SessionLocal is not initialized.")
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def update_all_time_high_leaderboard():
    """Calculates and caches the 'All time high' leaderboard."""
    print("Running job: update_all_time_high_leaderboard")
    db_gen = get_db_session_for_job()
    db = next(db_gen, None)
    if not db:
        return

    try:
        # Clear old 'all_time' entries
        db.query(Leaderboard).filter(Leaderboard.timespan == 'all_time').delete(synchronize_session=False)

        # Base query to rank users by their best scores
        # We use text() for the UNION and RANK() as it's cleaner
        sql_query = text("""
        WITH all_scores AS (
            SELECT 
                id as user_id, 
                username, 
                'easy' as difficulty, 
                best_score_easy as total_score 
            FROM users WHERE best_score_easy > 0
            UNION ALL
            SELECT 
                id as user_id, 
                username, 
                'medium' as difficulty, 
                best_score_medium as total_score 
            FROM users WHERE best_score_medium > 0
            UNION ALL
            SELECT 
                id as user_id, 
                username, 
                'hard' as difficulty, 
                best_score_hard as total_score 
            FROM users WHERE best_score_hard > 0
        ),
        ranked_scores AS (
            SELECT 
                user_id, 
                username, 
                difficulty, 
                total_score,
                RANK() OVER(PARTITION BY difficulty ORDER BY total_score DESC) as rank
            FROM all_scores
        )
        SELECT * FROM ranked_scores
        """)

        results = db.execute(sql_query).mappings().all()
        new_entries = []
        for row in results:
            new_entries.append(
                Leaderboard(
                    user_id=row['user_id'],
                    username=row['username'],
                    difficulty=row['difficulty'],
                    timespan='all_time',
                    total_score=row['total_score'],
                    rank=row['rank'],
                    last_updated=datetime.utcnow()
                )
            )
        
        db.add_all(new_entries)
        db.commit()
        print(f"Successfully updated 'all_time' leaderboard with {len(new_entries)} entries.")

    except Exception as e:
        print(f"Error updating 'all_time' leaderboard: {e}")
        db.rollback()
    finally:
        db.close()


def update_periodic_leaderboard(timespan: str = 'daily'):
    """Calculates and caches the 'daily' or 'weekly' leaderboard."""
    print(f"Running job: update_periodic_leaderboard for '{timespan}'")
    db_gen = get_db_session_for_job()
    db = next(db_gen, None)
    if not db:
        return

    try:
        # 1. Define time window
        now_utc = datetime.utcnow()
        if timespan == 'daily':
            start_time = datetime.combine(now_utc.date(), time.min)
        elif timespan == 'weekly':
            start_time = datetime.combine(now_utc.date() - timedelta(days=now_utc.weekday()), time.min)
        else:
            return # Invalid timespan
        
        # 2. Clear old entries
        db.query(Leaderboard).filter(Leaderboard.timespan == timespan).delete(synchronize_session=False)

        # 3. Build the complex query
        # This joins Games, Puzzles, and Users, finds the MAX score per user/difficulty
        # in the time window, and ranks them.
        sql_query = text("""
        WITH user_best_scores AS (
            SELECT
                g.user_id,
                u.username,
                p.difficulty,
                MAX(g.final_score) as max_score
            FROM games g
            JOIN users u ON g.user_id = u.id
            JOIN puzzles p ON g.puzzle_id = p.id
            WHERE g.was_completed = TRUE
              AND g.completed_at >= :start_time
              AND g.completed_at < :end_time
            GROUP BY g.user_id, u.username, p.difficulty
        ),
        ranked_scores AS (
            SELECT
                user_id,
                username,
                difficulty,
                max_score,
                RANK() OVER(PARTITION BY difficulty ORDER BY max_score DESC) as rank
            FROM user_best_scores
        )
        SELECT * FROM ranked_scores WHERE max_score > 0
        """)

        results = db.execute(sql_query, {"start_time": start_time, "end_time": now_utc}).mappings().all()

        new_entries = []
        for row in results:
            new_entries.append(
                Leaderboard(
                    user_id=row['user_id'],
                    username=row['username'],
                    difficulty=row['difficulty'],
                    timespan=timespan,
                    total_score=row['max_score'],
                    rank=row['rank'],
                    last_updated=datetime.utcnow()
                )
            )
        
        db.add_all(new_entries)
        db.commit()
        print(f"Successfully updated '{timespan}' leaderboard with {len(new_entries)} entries.")

    except Exception as e:
        print(f"Error updating '{timespan}' leaderboard: {e}")
        db.rollback()
    finally:
        db.close()