
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.interview_engine import (
    create_session,
    process_answer,
    get_session_report
)

router = APIRouter(
    prefix="/api/interview",
    tags=["Interview"]
)


class StartInterviewRequest(BaseModel):
    role: Literal[
        "React Developer",
        "Full Stack Developer",
        "Python Developer",
        "AI Engineer"
    ]

    difficulty: Literal[
        "beginner",
        "intermediate",
        "advanced"
    ] = "intermediate"


class AnswerRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=5000)


@router.post("/start")
async def start_interview(request: StartInterviewRequest):

    try:
        result = create_session(
            role=request.role,
            difficulty=request.difficulty
        )

        return {
            "message": "Interview started successfully.",
            **result
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not start interview: {str(error)}"
        )


@router.post("/respond")
async def respond(request: AnswerRequest):

    try:
        result = await process_answer(
            session_id=request.session_id,
            answer=request.message
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Interview processing failed: {str(error)}"
        )


@router.get("/report/{session_id}")
async def interview_report(session_id: str):

    try:
        return get_session_report(session_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate report: {str(error)}"
        )
