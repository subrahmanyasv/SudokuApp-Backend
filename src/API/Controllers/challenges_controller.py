# src/API/Controllers/challenge_controller.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
import datetime
from datetime import timedelta # Import timedelta

# --- Project-Specific Imports ---
from src.Models.TableModels import User, Puzzles, Challenges
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.challenges_schema import (
    ChallengeCreate,
    ChallengeRespond,
    ChallengeComplete,
    ChallengeResponse
)

# --- Helper Function for Eager Loading ---
def _get_challenge_query(db: Session):
    """Returns a query for Challenges with all relationships eager-loaded."""
    return db.query(Challenges).options(
        joinedload(Challenges.puzzle),
        joinedload(Challenges.challenger),
        joinedload(Challenges.opponent),
        joinedload(Challenges.winner) # Winner might be None, but load it anyway
    )

# --- Controller Functions ---

def create_challenge(user: TokenPayload, db: Session, challenge_data: ChallengeCreate) -> ChallengeResponse:
    """
    Creates a new challenge from the current user to an opponent.
    """
    try:
        challenger_id = user.id
        opponent_id = challenge_data.opponent_id

        # 1. Validation Checks
        if challenger_id == opponent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot challenge yourself."
            )

        opponent = db.query(User).filter(User.id == opponent_id).first()
        if not opponent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {opponent_id} not found."
            )

        puzzle = db.query(Puzzles).filter(Puzzles.id == challenge_data.puzzle_id).first()
        if not puzzle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Puzzle with id {challenge_data.puzzle_id} not found."
            )
        
        # Check for existing pending challenge between these users for this puzzle
        existing_challenge = db.query(Challenges).filter(
            Challenges.puzzle_id == challenge_data.puzzle_id,
            Challenges.challenger_id == challenger_id,
            Challenges.opponent_id == opponent_id,
            Challenges.status == "pending"
        ).first()

        if existing_challenge:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending challenge to this user for this puzzle already exists."
            )

        # 2. Create New Challenge
        expires_at = datetime.datetime.utcnow() + timedelta(days=2) # Challenge expires in 48 hours

        new_challenge = Challenges(
            puzzle_id=challenge_data.puzzle_id,
            challenger_id=challenger_id,
            opponent_id=opponent_id,
            status="pending",
            challenger_duration=challenge_data.challenger_duration,
            expires_at=expires_at
        )

        db.add(new_challenge)
        db.commit()
        db.refresh(new_challenge)

        # 3. Fetch the full data for the response
        # We query it again using the helper to load all relationships
        response_data = _get_challenge_query(db).filter(Challenges.id == new_challenge.id).first()
        
        if not response_data:
             # This should not happen, but good to check
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve challenge after creation.")

        return response_data

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error creating challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred while creating the challenge."
        )


def get_my_challenges(user: TokenPayload, db: Session) -> List[ChallengeResponse]:
    """
    Retrieves all challenges (pending, active, completed) where the user
    is either the challenger or the opponent.
    """
    try:
        user_id = user.id
        
        # Use the helper to get the base query with eager loading
        challenges = _get_challenge_query(db).filter(
                Challenges.opponent_id == user_id,
                Challenges.status == "pending"
        ).order_by(Challenges.created_at.desc()).all()

        return challenges

    except Exception as e:
        db.rollback() 
        print(f"Error getting challenges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred while fetching challenges."
        )


def respond_to_challenge(user: TokenPayload, db: Session, challenge_id: UUID, response_data: ChallengeRespond) -> ChallengeResponse:
    """
    Allows a user (opponent) to accept or reject a 'pending' challenge.
    """
    try:
        user_id = user.id

        # Find the challenge, ensuring user is the opponent and it's pending
        challenge = _get_challenge_query(db).filter(
            Challenges.id == challenge_id,
            Challenges.opponent_id == user_id,
            Challenges.status == "pending"
        ).first()

        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending challenge not found or you do not have permission to respond."
            )

        # Update status based on action
        if response_data.action == "accept":
            challenge.status = "accepted"
        elif response_data.action == "reject":
            challenge.status = "rejected"
        
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        
        return challenge

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error responding to challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred while responding to the challenge."
        )


def complete_challenge(user: TokenPayload, db: Session, challenge_id: UUID, completion_data: ChallengeComplete) -> ChallengeResponse:
    """
    Allows the opponent to submit their score for an 'accepted' challenge.
    This action marks the challenge as 'completed' and determines a winner.
    """
    try:
        user_id = user.id

        # Find the challenge, ensuring user is the opponent and it's accepted
        challenge = _get_challenge_query(db).filter(
            Challenges.id == challenge_id,
            Challenges.opponent_id == user_id,
            Challenges.status == "accepted"
        ).first()

        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Accepted challenge not found or you do not have permission to complete it."
            )
        
        # 1. Set opponent's score
        challenge.opponent_duration = completion_data.opponent_duration

        # 2. Determine winner (tie goes to challenger)
        if completion_data.opponent_duration < challenge.challenger_duration:
            challenge.winner_id = user_id # Opponent wins
        else:
            challenge.winner_id = challenge.challenger_id # Challenger wins

        # 3. Update status
        challenge.status = "completed"
        challenge.completed_at = datetime.datetime.utcnow()

        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        
        # 4. Return the fully populated, completed challenge
        return challenge

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Error completing challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred while completing the challenge."
        )
