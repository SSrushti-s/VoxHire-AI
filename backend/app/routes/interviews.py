
from typing import Literal

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.interview_engine import (
    create_session,
    process_answer,
    get_session_report,
    personalize_opening_question,
    sessions
)
from app.services.jd_analysis_service import analyze_job_description

router = APIRouter(prefix="/api/interview", tags=["Interview"])


class StartInterviewRequest(BaseModel):
    interview_mode: Literal["role", "job_description"] = "role"
    role: Literal[
        "React Developer",
        "Full Stack Developer",
        "Python Developer",
        "AI Engineer"
    ] | None = None

    job_description: str | None = Field(default=None, max_length=15000)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    resume_id: str | None = None


class AnswerRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=5000)


def verify_session_owner(session_id: str, user_id: str):
    session = sessions.get(session_id)

    # Return the same response for missing and other users' sessions
    if not session or session.get("candidate_id") != user_id:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found."
        )

    return session


@router.post("/start")
async def start_interview(
    request: StartInterviewRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = str(current_user["_id"])

        jd_analysis = None

        if request.interview_mode == "role":
            if not request.role:
                raise ValueError("Please select a job role.")
            selected_role = request.role
        else:
            if not request.job_description or not request.job_description.strip():
                raise ValueError("Please enter a job description.")

            selected_role = None
            jd_analysis = await analyze_job_description(
                request.job_description
            )

        result = create_session(
            role=selected_role,
            difficulty=request.difficulty,
            resume_id=request.resume_id,
            interview_mode=request.interview_mode,
            job_description=request.job_description,
            jd_analysis=jd_analysis,
            candidate_id=user_id
        )

        try:
            question = await personalize_opening_question(
                result["session_id"]
            )
            result["question"] = question
        except Exception as error:
            print("OPENING QUESTION PERSONALIZATION FAILED:", error)

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        print("INTERVIEW START ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not start interview."
        )


@router.post("/respond")
async def respond(
    request: AnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    verify_session_owner(request.session_id, user_id)

    try:
        result = await process_answer(
            session_id=request.session_id,
            answer=request.message
        )
        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        print("INTERVIEW RESPONSE ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Interview processing failed."
        )


@router.get("/report/{session_id}")
async def interview_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    verify_session_owner(session_id, user_id)

    try:
        return get_session_report(session_id)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not generate report."
        )
