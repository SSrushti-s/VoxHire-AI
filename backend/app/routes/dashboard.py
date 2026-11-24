
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.persistance_service import (
    save_interview,
    get_interview_history,
    get_interview_by_id,
    get_dashboard_summary
)

from app.services.interview_engine import sessions

router = APIRouter()


class SaveInterviewRequest(BaseModel):
    session_id: str
    role: str
    difficulty: str
    report: dict[str, Any]


@router.post("/interviews")
async def save_completed_interview(
    request: SaveInterviewRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    session = sessions.get(request.session_id)

    if not session or session.get("candidate_id") != user_id:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found."
        )

    # The interview engine already saves completed interviews.
    # Avoid creating a duplicate record.
    if session.get("persisted_interview_id"):
        return {
            "message": "Interview already saved.",
            "interview_id": session["persisted_interview_id"]
        }

    try:
        interview_id = await save_interview(
            candidate_id=user_id,
            session_id=request.session_id,
            role=request.role,
            difficulty=request.difficulty,
            report=request.report
        )

        session["persisted_interview_id"] = interview_id

        return {
            "message": "Interview saved successfully.",
            "interview_id": interview_id
        }

    except Exception as error:
        print("SAVE INTERVIEW ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not save interview."
        )


@router.get("/interviews")
async def interview_history(
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    try:
        return await get_interview_history(user_id)
    except Exception as error:
        print("INTERVIEW HISTORY ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve interview history."
        )


@router.get("/summary")
async def dashboard_summary(
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    try:
        return await get_dashboard_summary(user_id)
    except Exception as error:
        print("DASHBOARD SUMMARY ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve dashboard summary."
        )


@router.get("/interview/{interview_id}")
async def interview_details(
    interview_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    interview = await get_interview_by_id(
        interview_id,
        user_id
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )

    return interview
