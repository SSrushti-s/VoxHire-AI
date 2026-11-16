
import uuid
from datetime import datetime, timezone

from app.services.evaluation_service import evaluate_answer
from app.services.intent_service import detect_intent

INTERVIEW_PHASES = [
    {
        "name": "Introduction",
        "max_questions": 1
    },
    {
        "name": "Fundamentals",
        "max_questions": 2
    },
    {
        "name": "Core Technical Concepts",
        "max_questions": 2
    },
    {
        "name": "Practical Scenarios",
        "max_questions": 2
    }
]


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


def create_session(role: str, difficulty: str):

    session_id = str(uuid.uuid4())

    session = {
        "session_id": session_id,
        "role": role,
        "difficulty": difficulty,
        "phase_index": 0,
        "questions_in_phase": 0,
        "follow_up_count": 0,
        "current_question": ROLE_OPENING_QUESTIONS[role],
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
        "difficulty": difficulty,
        "phase": INTERVIEW_PHASES[0]["name"],
        "question": session["current_question"]
    }



async def process_answer(session_id: str, answer: str):

    session = sessions.get(session_id)

    if not session:
        raise ValueError("Interview session not found.")

    if session["completed"]:
        raise ValueError("This interview has already been completed.")

    if not answer.strip():
        raise ValueError("Answer cannot be empty.")

    # -------------------------------------------------
    # STEP 1: Handle pending interview-end confirmation
    # -------------------------------------------------

    if session["pending_end_confirmation"]:

        message = answer.strip().lower()

        yes_responses = {
            "yes", "yes please", "yeah", "yep",
            "sure", "confirm", "end it", "please do"
        }

        no_responses = {
            "no", "no thanks", "nope",
            "continue", "keep going", "not yet"
        }

        if message in yes_responses:

            session["pending_end_confirmation"] = False
            session["completed"] = True

            report = generate_report(session)

            return {
                "session_id": session_id,
                "response": (
                    "Your interview has been ended. "
                    "Here is your final performance report."
                ),
                "evaluation": None,
                "current_phase": "Completed",
                "difficulty": session["difficulty"],
                "interview_completed": True,
                "report": report
            }

        elif message in no_responses:

            session["pending_end_confirmation"] = False

            return {
                "session_id": session_id,
                "response": (
                    "No problem! Let's continue. "
                    + session["current_question"]
                ),
                "evaluation": None,
                "current_phase": INTERVIEW_PHASES[
                    session["phase_index"]
                ]["name"],
                "difficulty": session["difficulty"],
                "interview_completed": False,
                "report": None
            }

        else:

            return {
                "session_id": session_id,
                "response": (
                    "Please say yes if you want to end the interview, "
                    "or no if you want to continue."
                ),
                "evaluation": None,
                "current_phase": INTERVIEW_PHASES[
                    session["phase_index"]
                ]["name"],
                "difficulty": session["difficulty"],
                "interview_completed": False,
                "report": None
            }


    # -------------------------------------------------
    # STEP 2: Detect candidate's intention
    # -------------------------------------------------

    try:
        intent = await detect_intent(answer)
        print("CANDIDATE MESSAGE:", answer)
        print("PROCESSED INTENT:", intent)

    except Exception as error:
        print("Intent detection failed:", error)

        # If intent detection fails, treat the message
        # as an attempted interview answer.
        intent = "ANSWER"


    # -------------------------------------------------
    # STEP 3: Handle non-answer messages
    # -------------------------------------------------

    current_phase = INTERVIEW_PHASES[
        session["phase_index"]
    ]["name"]


    # Candidate wants the question repeated.
    if intent == "REPEAT":

        return {
            "session_id": session_id,
            "response": session["current_question"],
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": False,
            "report": None
        }


    # Candidate wants clarification.
    if intent == "CLARIFY":

        return {
            "session_id": session_id,
            "response": (
                "Certainly! I can clarify the question. "
                "Please tell me which part you would like me to explain. "
                "The current question is: "
                + session["current_question"]
            ),
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": False,
            "report": None
        }


    # Candidate requests a hint.
    if intent == "HINT":

        return {
            "session_id": session_id,
            "response": (
                "Here's a small hint: think about the main purpose "
                "of the concept, how it works internally, and where "
                "you would use it in a practical application. "
                "Try answering in your own words. "
                "Your question is: "
                + session["current_question"]
            ),
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": False,
            "report": None
        }


    # Candidate requests a progress or final report.
    if intent == "REPORT_REQUEST":

        report = generate_report(session)

        if session["completed"]:
            report_message = (
                "Your final interview report is ready. "
            )
        else:
            report_message = (
                "Your interview is still in progress. "
                "Here is your progress report so far. "
            )

        report_message += (
            f"You have submitted {report['total_answers']} answers. "
            f"Your current average score is "
            f"{report['overall_score']} out of 10. "
        )

        if report["strengths"]:
            report_message += (
                "Your strengths include: "
                + ", ".join(report["strengths"][:3])
                + ". "
            )

        if report["improvements"]:
            report_message += (
                "Areas to improve include: "
                + ", ".join(report["improvements"][:3])
                + ". "
            )

        if not session["completed"]:
            report_message += (
                "Let's continue with your current question: "
                + session["current_question"]
            )

        return {
            "session_id": session_id,
            "response": report_message,
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": session["completed"],
            "report": report
        }


    # Candidate explicitly wants to end the interview.
    if intent == "END_INTERVIEW":

        session["pending_end_confirmation"] = True

        return {
            "session_id": session_id,
            "response": (
                "Are you sure you want to end this interview? "
                "Say yes to finish and generate your final report, "
                "or no to continue."
            ),
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": False,
            "report": None
        }


    # General conversation or unrelated message.
    if intent == "OTHER":

        return {
            "session_id": session_id,
            "response": (
                "I'm here to help with your interview. "
                "You can answer the current question, ask for a hint, "
                "request clarification, or ask for your progress report. "
                "Your current question is: "
                + session["current_question"]
            ),
            "evaluation": None,
            "current_phase": current_phase,
            "difficulty": session["difficulty"],
            "interview_completed": False,
            "report": None
        }


    # -------------------------------------------------
    # STEP 4: Evaluate actual candidate answer
    # -------------------------------------------------

    phase = INTERVIEW_PHASES[session["phase_index"]]

    next_phase_index = session["phase_index"]

    if (
        session["questions_in_phase"] + 1
        >= phase["max_questions"]
    ):
        next_phase_index += 1

    if next_phase_index < len(INTERVIEW_PHASES):
        next_phase = INTERVIEW_PHASES[next_phase_index]["name"]
    else:
        next_phase = "Interview completed"

    follow_up_allowed = session["follow_up_count"] == 0

    evaluation = await evaluate_answer(
        role=session["role"],
        difficulty=session["difficulty"],
        phase=phase["name"],
        question=session["current_question"],
        answer=answer,
        next_phase=next_phase,
        follow_up_allowed=follow_up_allowed,
        previous_answers=session["answers"]
    )


    # -------------------------------------------------
    # STEP 5: Store answer and evaluation
    # -------------------------------------------------

    record = {
        "phase": phase["name"],
        "question": session["current_question"],
        "answer": answer,
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "strengths": evaluation["strengths"],
        "improvements": evaluation["improvements"]
    }

    session["answers"].append(record)
    session["scores"].append(evaluation["score"])


    # -------------------------------------------------
    # STEP 6: Decide follow-up or next question
    # -------------------------------------------------

    ask_follow_up = (
        evaluation["ask_follow_up"] and follow_up_allowed
    )

    if ask_follow_up:

        session["follow_up_count"] += 1

        next_question = evaluation["next_question"]

    else:

        session["questions_in_phase"] += 1
        session["follow_up_count"] = 0

        if (
            session["questions_in_phase"]
            >= phase["max_questions"]
        ):

            session["phase_index"] += 1
            session["questions_in_phase"] = 0

        if session["phase_index"] >= len(INTERVIEW_PHASES):

            session["completed"] = True

            next_question = (
                "Thank you! You have completed your interview. "
                "Here is your performance summary."
            )

        else:

            next_question = evaluation["next_question"]


    # -------------------------------------------------
    # STEP 7: Protect against empty questions
    # -------------------------------------------------

    if not next_question.strip():

        next_question = (
            "Let's move on. Can you explain your approach in more detail?"
        )


    # -------------------------------------------------
    # STEP 8: Update session state
    # -------------------------------------------------

    session["difficulty"] = evaluation["next_difficulty"]

    session["current_question"] = next_question

    report = None

    if session["completed"]:
        report = generate_report(session)


    # -------------------------------------------------
    # STEP 9: Return result to React frontend
    # -------------------------------------------------

    return {
        "session_id": session_id,

        "response": next_question,

        "evaluation": {
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "strengths": evaluation["strengths"],
            "improvements": evaluation["improvements"]
        },

        "current_phase": (
            "Completed"
            if session["completed"]
            else INTERVIEW_PHASES[
                session["phase_index"]
            ]["name"]
        ),

        "difficulty": session["difficulty"],

        "interview_completed": session["completed"],

        "report": report
    }



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

    # Remove duplicate feedback items.
    strengths = list(dict.fromkeys(all_strengths))
    improvements = list(dict.fromkeys(all_improvements))

    return {
        "role": session["role"],
        "total_answers": len(scores),
        "overall_score": average_score,
        "max_score": 10,
        "strengths": strengths[:5],
        "improvements": improvements[:5],
        "answers": session["answers"]
    }


def get_session_report(session_id: str):

    session = sessions.get(session_id)

    if not session:
        raise ValueError("Interview session not found.")

    if not session["completed"]:
        raise ValueError("Interview has not been completed yet.")

    return generate_report(session)
