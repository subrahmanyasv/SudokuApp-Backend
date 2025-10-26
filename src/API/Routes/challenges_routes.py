# src/API/Routes/challenge_routes.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

# --- Project-Specific Imports ---
from src.Config.database import get_db_session
from src.Security.security import validate_user
from src.API.Controllers import challenges_controller
from src.Schemas.auth_schema import TokenPayload
from src.Schemas.challenges_schema import (
    ChallengeCreate,
    ChallengeRespond,
    ChallengeComplete,
    ChallengeResponse
)

router = APIRouter()

@router.post(
    "/",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Challenge"
)
def create_challenge_route(
    challenge_data: ChallengeCreate, # This is the request body
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Creates a new challenge. The authenticated user is the challenger.
    This is typically called after the challenger completes a game,
    and their score/duration is passed in `challenge_data`.
    """
    try:
        return challenges_controller.create_challenge(user, db, challenge_data)
    except HTTPException as http_exc:
        # Re-raise known exceptions from the controller
        raise http_exc
    except Exception as e:
        print(f"Error creating challenge in router: {e}")
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {e}"
        )


@router.get(
    "/",
    response_model=List[ChallengeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Pending Incoming Challenges"
)
def get_my_challenges_route(
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches all challenges for the authenticated user where they
    are the *opponent* and the challenge status is *pending*.
    
    (This route reflects your modified get_my_challenges controller logic)
    """
    try:
        return challenges_controller.get_my_challenges(user, db)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error getting challenges in router: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {e}"
        )


@router.post(
    "/{challenge_id}/respond",
    response_model=ChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Respond to a Challenge (Accept/Reject)"
)
def respond_to_challenge_route(
    challenge_id: UUID,                 # From the URL path
    response_data: ChallengeRespond,    # From the request body
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Allows the authenticated user (who must be the opponent) to
    accept or reject a *pending* challenge.
    """
    try:
        return challenges_controller.respond_to_challenge(user, db, challenge_id, response_data)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error responding to challenge in router: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {e}"
        )


@router.post(
    "/{challenge_id}/complete",
    response_model=ChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete an Accepted Challenge and Submit Score"
)
def complete_challenge_route(
    challenge_id: UUID,                   # From the URL path
    completion_data: ChallengeComplete,   # From the request body
    user: TokenPayload = Depends(validate_user),
    db: Session = Depends(get_db_session)
):
    """
    Allows the authenticated user (who must be the opponent) to
    submit their final time for an *accepted* challenge.
    This marks the challenge as 'completed' and determines a winner.
    """
    try:
        return challenges_controller.complete_challenge(user, db, challenge_id, completion_data)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error completing challenge in router: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {e}"
        )
