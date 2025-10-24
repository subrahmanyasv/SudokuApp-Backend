from sqlalchemy.orm import Session
from typing import List, Dict
from src.Models.TableModels import Puzzles

def get_games_count_util(db: Session) -> int:
        count = db.query(Puzzles).count()
        return count

def add_games_to_db_util(db: Session, games: List[Dict[str, str]] = [], difficulty: str = "easy"):
    
    for game in games:
        db.add(Puzzles(**game, difficulty=difficulty))
    db.commit()