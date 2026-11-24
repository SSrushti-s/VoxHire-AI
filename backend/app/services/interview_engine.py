
import uuid
from datetime import datetime, timezone

from app.services.interview_graph import run_interview_workflow
from app.services.retrieval_service import search_resume
from app.services.question_service import generate_personalized_question
from app.services.jd_question_service import generate_jd_opening_question
from app.services.interview_config import INTERVIEW_PHASES
from app.services.persistance_service import save_interview

ROLE_OPENING_QUESTIONS = {
    "React Developer":
        "To begin, tell me about your experience with JavaScript and React. Have you built any projects using them?",

    "Full Stack Developer":
        "Tell me about a full-stack application you have built. What technologies did you use for the frontend and backend?",

    "Python Developer":
        "Tell me about your experience with Python and the types of applications you have developed.",

    "AI Engineer":
        "Tell me about your experience with artificial intelligence, machine learning or generative AI projects."
}


# Temporary in-memory session storage
sessions = {}


def create_session(
    role: str,
    difficulty: str,
    resume_id: str = None,
    interview_mode: str = "role",
    job_description: str = None,
    jd_analysis: dict = None,
    candidate_id: str = None
):

    if interview_mode not in ["role", "job_description"]:
        raise ValueError("Invalid interview mode.")

    if interview_mode == "role":
        if role not in ROLE_OPENING_QUESTIONS:
            raise ValueError("Please select a valid job role.")

        opening_question = ROLE_OPENING_QUESTIONS[role]

    else:
        if not jd_analysis:
            raise ValueError("Job description analysis is required.")

        role = jd_analysis.get("job_title") or "Job Description Position"

        opening_question = (
            f"Let's discuss your suitability for the {role} position. "
            "Could you briefly introduce your relevant experience?"
        )

    session_id = str(uuid.uuid4())

    session = {
        "session_id": session_id,
        "resume_id": resume_id,
        "candidate_id": candidate_id,
        "persisted_interview_id": None,
        "interview_mode": interview_mode,
        "job_description": job_description,
        "jd_analysis": jd_analysis,
        "covered_skills": [],
        "role": role,
        "difficulty": difficulty,
        "asked_questions": [opening_question],

        "main_questions_count": 0,

        "max_main_questions": 10,

        "current_target_skill": None,
        "phase_index": 0,
        "questions_in_phase": 0,
        "follow_up_count": 0,

        "current_question": opening_question,

        "answers": [],
        "scores": [],

        "completed": False,
        "pending_end_confirmation": False,

        "created_at": datetime.now(timezone.utc).isoformat()
    }

    sessions[session_id] = session

    return {
        "session_id": session_id,
        "role": role,
        "interview_mode": interview_mode,
        "difficulty": difficulty,
        "phase": INTERVIEW_PHASES[0]["name"],
        "question": session["current_question"]
    }



async def process_answer(session_id: str, answer: str):

    result = await run_interview_workflow(
        session_id=session_id,
        answer=answer,
        session_store=sessions,
        report_generator=generate_report
    )

    session = sessions.get(session_id)

    # Save only after the interview has been completed.
    if (
        result.get("interview_completed")
        and session
        and not session.get("persisted_interview_id")
    ):

        report = result.get("report") or generate_report(session)

        try:

            interview_id = await save_interview(
                candidate_id=session["candidate_id"],
                session_id=session_id,
                role=session["role"],
                difficulty=session["difficulty"],
                report=report
            )

            # Remember the MongoDB ID to prevent duplicate saves.
            session["persisted_interview_id"] = interview_id

            result["persistence_saved"] = True

            print(
                "INTERVIEW SAVED TO MONGODB:",
                interview_id
            )

        except Exception as error:

            print("INTERVIEW PERSISTENCE ERROR:", error)

            result["persistence_saved"] = False
            result["persistence_error"] = (
                "Interview completed, but saving to MongoDB failed."
            )

    return result



def generate_report(session: dict):

    scores = session["scores"]

    average_score = (
        round(sum(scores) / len(scores), 2)
        if scores else 0
    )

    all_strengths = []
    all_improvements = []

    for answer in session["answers"]:
        all_strengths.extend(answer["strengths"])
        all_improvements.extend(answer["improvements"])

    strengths = list(dict.fromkeys(all_strengths))
    improvements = list(dict.fromkeys(all_improvements))

    jd_analysis = session.get("jd_analysis") or {}

    required_skills = jd_analysis.get("required_skills", [])
    preferred_skills = jd_analysis.get("preferred_skills", [])

    covered_skills = session.get("covered_skills", [])

    covered_lookup = {
        skill.casefold() for skill in covered_skills
    }

    uncovered_required = [
        skill
        for skill in required_skills
        if skill.casefold() not in covered_lookup
    ]

    required_coverage = (
        round(
            (
                len(required_skills) - len(uncovered_required)
            ) / len(required_skills) * 100,
            2
        )
        if required_skills else None
    )
    return {
        "role": session["role"],
        "interview_mode": session.get("interview_mode", "role"),
        "total_answers": len(scores),
        "overall_score": average_score,
        "max_score": 10,
        "strengths": strengths[:5],
        "improvements": improvements[:5],
        "answers": session["answers"],
        "skill_coverage": {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "assessed_skills": covered_skills,
            "unassessed_required_skills": uncovered_required,
            "required_coverage_percentage": required_coverage
        },
        "main_questions_count": session.get(
            "main_questions_count", 0
        ),

        "final_difficulty": session["difficulty"],

        "questions_asked": len(
            session.get("asked_questions", [])
        )
    }


def get_session_report(session_id: str):

    session = sessions.get(session_id)

    if not session:
        raise ValueError("Interview session not found.")

    if not session["completed"]:
        raise ValueError("Interview has not been completed yet.")

    return generate_report(session)


async def personalize_opening_question(session_id: str):

    session = sessions.get(session_id)

    if not session:
        raise ValueError("Interview session not found.")

    resume_context = ""
    resume_id = session.get("resume_id")

    # Retrieve resume information if available
    if resume_id:

        if session["interview_mode"] == "job_description":

            jd_analysis = session["jd_analysis"]

            search_query = " ".join(
                jd_analysis.get("required_skills", [])
                + jd_analysis.get("preferred_skills", [])
                + jd_analysis.get("interview_focus_areas", [])
            )

        else:
            search_query = (
                f"Projects, technical skills, experience and "
                f"technologies relevant to a {session['role']} position"
            )

        retrieved_chunks = search_resume(
            resume_id=resume_id,
            query=search_query,
            owner_id=session.get("candidate_id"),
            top_k=4
        )

        if retrieved_chunks:
            resume_context = "\n\n".join(
                item["text"] for item in retrieved_chunks
            )

    # JD-based opening question
    if session["interview_mode"] == "job_description":

        question = await generate_jd_opening_question(
            difficulty=session["difficulty"],
            jd_analysis=session["jd_analysis"],
            resume_context=resume_context
        )

    # Existing role-based opening question
    else:

        if not resume_context:
            return session["current_question"]

        question = await generate_personalized_question(
            role=session["role"],
            difficulty=session["difficulty"],
            resume_context=resume_context
        )

    session["current_question"] = question

    print("PERSONALIZED OPENING QUESTION:", question)

    return question
