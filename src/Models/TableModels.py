# SudokuApp-Backend/src/Models/TableModels.py

import uuid
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import relationship
import datetime # Import datetime

from src.Config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


    total_games_played = Column(Integer, default=0, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    best_score_easy = Column(Integer, default=0, nullable=False)
    best_score_medium = Column(Integer, default=0, nullable=False)
    best_score_hard = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    games = relationship("Games", back_populates="user")
    challenger_challenges = relationship("Challenges", foreign_keys="Challenges.challenger_id", back_populates="challenger")
    opponent_challenges = relationship("Challenges", foreign_keys="Challenges.opponent_id", back_populates="opponent")
    won_challenges = relationship("Challenges", foreign_keys="Challenges.winner_id", back_populates="winner")
    leaderboard_entries = relationship("Leaderboard", back_populates="user")

class Puzzles(Base):
    __tablename__ = "puzzles"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    difficulty = Column(String(10), index=True, nullable=False) # Good to have a length
    board_string = Column(String(81), nullable=False)
    solution_string = Column(String(81), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False) # A single game is used only once.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    games = relationship("Games", back_populates="puzzle")
    challenges = relationship("Challenges", back_populates="puzzle")

class Games(Base):
    __tablename__ = "games"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    puzzle_id = Column(pgUUID(as_uuid=True), ForeignKey("puzzles.id"), nullable=False)

    was_completed = Column(Boolean, default=False, nullable=False)
    duration_seconds = Column(Integer, default= 0)
    errors_made = Column(Integer, default=0, nullable=False)
    hints_used = Column(Integer, default=0, nullable=False)
    final_score = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # *** ADDED: Column to store the current state of the board ***
    current_state = Column(String(81), nullable=True) # 81 chars for the board

    # *** ADDED: Timestamp for last played/saved action ***
    last_played = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


    user = relationship("User", back_populates="games")
    puzzle = relationship("Puzzles", back_populates="games")

class Challenges(Base):
    __tablename__ = "challenges"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    puzzle_id = Column(pgUUID(as_uuid=True), ForeignKey("puzzles.id"), nullable=False)
    challenger_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    opponent_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(15), default="pending", nullable=False)  # pending, accepted, declined, completed, expired
    challenger_duration = Column(Integer)
    opponent_duration = Column(Integer)
    winner_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    puzzle = relationship("Puzzles", back_populates="challenges")
    challenger = relationship("User", foreign_keys=[challenger_id], back_populates="challenger_challenges")
    opponent = relationship("User", foreign_keys=[opponent_id], back_populates="opponent_challenges")
    winner = relationship("User", foreign_keys=[winner_id], back_populates="won_challenges")

class Leaderboard(Base):
    __tablename__ = "leaderboard_cache"

    # Composite Primary Key
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    difficulty = Column(String(10), primary_key=True)
    timespan = Column(String(10), primary_key=True)
    username = Column(String(50), nullable=False)
    total_score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="leaderboard_entries")
