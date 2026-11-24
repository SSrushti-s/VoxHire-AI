
from typing import TypedDict, Callable, Any
import re
from langgraph.graph import StateGraph, START, END

from app.services.intent_service import detect_intent
from app.services.retrieval_service import search_resume
from app.services.evaluation_service import evaluate_answer
from app.services.interview_config import INTERVIEW_PHASES

# =========================================================
# PART 1: ORIGINAL STAGE 4.1 BASIC GRAPH
# Keep this so your original test still works.
# =========================================================

class InterviewState(TypedDict):
    candidate_answer: str
    role: str
    is_valid: bool
    response: str


def validate_answer(state: InterviewState):
    answer = state["candidate_answer"]

    if not answer or not answer.strip():
        return {
            "is_valid": False,
            "response": "Please provide an answer."
        }

    return {
        "is_valid": True,
        "response": "Answer received successfully."
    }


def route_answer(state: InterviewState):
    if state["is_valid"]:
        return "process_answer"

    return END


def process_basic_answer(state: InterviewState):
    answer = state["candidate_answer"]
    role = state["role"]

    return {
        "response": (
            f"Your answer for the {role} interview "
            f"has been received: {answer}"
        )
    }


basic_builder = StateGraph(InterviewState)

basic_builder.add_node("validate_answer", validate_answer)
basic_builder.add_node("process_answer", process_basic_answer)

basic_builder.add_edge(START, "validate_answer")

basic_builder.add_conditional_edges(
    "validate_answer",
    route_answer
)

basic_builder.add_edge("process_answer", END)

interview_graph = basic_builder.compile()


async def run_interview_graph(candidate_answer: str, role: str):
    result = await interview_graph.ainvoke({
        "candidate_answer": candidate_answer,
        "role": role,
        "is_valid": False,
        "response": ""
    })

    return result


# =========================================================
# PART 2: ACTUAL VOXHIRE INTERVIEW GRAPH - STAGE 4.2
# =========================================================

class VoxHireState(TypedDict, total=False):

    session_id: str
    answer: str

    session_store: dict
    session: dict

    report_generator: Callable

    is_pending_confirmation: bool

    intent: str
    resume_context: str

    phase: dict
    next_phase: str
    follow_up_allowed: bool

    evaluation: dict
    result: dict


# ---------------------------------------------------------
# NODE 1: LOAD AND VALIDATE INTERVIEW SESSION
# ---------------------------------------------------------

def load_session(state: VoxHireState):

    session_id = state["session_id"]
    answer = state["answer"]

    session = state["session_store"].get(session_id)

    if not session:
        raise ValueError("Interview session not found.")

    if session["completed"]:
        raise ValueError(
            "This interview has already been completed."
        )

    if not answer.strip():
        raise ValueError("Answer cannot be empty.")

    return {
        "session": session,
        "is_pending_confirmation": session[
            "pending_end_confirmation"
        ]
    }


# ---------------------------------------------------------
# ROUTE 1: CHECK WHETHER END CONFIRMATION IS PENDING
# ---------------------------------------------------------

def route_after_load(state: VoxHireState):

    if state["is_pending_confirmation"]:
        return "pending"

    return "intent"


# ---------------------------------------------------------
# NODE 2: HANDLE PENDING END CONFIRMATION
# ---------------------------------------------------------


def handle_pending_confirmation(state: VoxHireState):

    session = state["session"]

    # Normalize the speech transcript.
    answer = state["answer"].strip().lower()
    answer = re.sub(r"[^\w\s']", "", answer)
    answer = re.sub(r"\s+", " ", answer).strip()

    print("END CONFIRMATION INPUT:", repr(answer))

    yes_responses = {
        "yes", "yes please", "yeah", "yeah please",
        "yep", "yep please", "sure", "sure thing",
        "absolutely", "correct", "affirmative",
        "confirm", "end it", "please do",
        "i do", "yes end it"
    }

    no_responses = {
        "no", "no thanks", "nope", "nah",
        "continue", "keep going", "not yet",
        "no please", "no i don't"
    }

    # Check negative responses first.
    if (
        answer in no_responses
        or re.match(r"^(no|nope|nah)\b", answer)
    ):

        session["pending_end_confirmation"] = False

        result = {
            "session_id": state["session_id"],
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

    # Check affirmative responses.
    elif (
        answer in yes_responses
        or re.match(
            r"^(yes|yeah|yep|sure|absolutely|correct|affirmative)\b",
            answer
        )
    ):

        print("CANDIDATE CONFIRMED INTERVIEW END")

        session["pending_end_confirmation"] = False
        session["completed"] = True

        report = state["report_generator"](session)

        result = {
            "session_id": state["session_id"],
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

    # Neither yes nor no.
    else:

        result = {
            "session_id": state["session_id"],
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

    return {"result": result}



# ---------------------------------------------------------
# NODE 3: DETECT CANDIDATE INTENT
# ---------------------------------------------------------

async def detect_intent_node(state: VoxHireState):

    intent = await detect_intent(state["answer"])

    print("CANDIDATE MESSAGE:", state["answer"])
    print("PROCESSED INTENT:", intent)

    return {"intent": intent}


# ---------------------------------------------------------
# ROUTE 2: DECIDE WHETHER THIS IS AN ANSWER
# ---------------------------------------------------------

def route_after_intent(state: VoxHireState):

    if state["intent"] == "ANSWER":
        return "answer"

    return "non_answer"


# ---------------------------------------------------------
# NODE 4: HANDLE HINT, REPEAT, CLARIFY, REPORT, ETC.
# ---------------------------------------------------------

def handle_non_answer(state: VoxHireState):

    session = state["session"]
    intent = state["intent"]

    from app.services.interview_engine import INTERVIEW_PHASES

    current_phase = INTERVIEW_PHASES[
        session["phase_index"]
    ]["name"]

    if intent == "REPEAT":

        response = session["current_question"]
        report = None

    elif intent == "CLARIFY":

        response = (
            "Certainly! I can clarify the question. "
            "Please tell me which part you would like me to explain. "
            "The current question is: "
            + session["current_question"]
        )
        report = None

    elif intent == "HINT":

        response = (
            "Here's a small hint: think about the main purpose "
            "of the concept, how it works internally, and where "
            "you would use it in a practical application. "
            "Try answering in your own words. "
            "Your question is: "
            + session["current_question"]
        )
        report = None

    elif intent == "REPORT_REQUEST":

        report = state["report_generator"](session)

        response = (
            "Your interview is still in progress. "
            "Here is your progress report so far. "
            f"You have submitted {report['total_answers']} answers. "
            f"Your current average score is "
            f"{report['overall_score']} out of 10. "
        )

        if report["strengths"]:
            response += (
                "Your strengths include: "
                + ", ".join(report["strengths"][:3])
                + ". "
            )

        if report["improvements"]:
            response += (
                "Areas to improve include: "
                + ", ".join(report["improvements"][:3])
                + ". "
            )

        response += (
            "Let's continue with your current question: "
            + session["current_question"]
        )

    elif intent == "END_INTERVIEW":

        session["pending_end_confirmation"] = True

        response = (
            "Are you sure you want to end this interview? "
            "Say yes to finish and generate your final report, "
            "or no to continue."
        )

        report = None

    else:

        response = (
            "I'm here to help with your interview. "
            "You can answer the current question, ask for a hint, "
            "request clarification, or ask for your progress report. "
            "Your current question is: "
            + session["current_question"]
        )

        report = None

    result = {
        "session_id": state["session_id"],
        "response": response,
        "evaluation": None,
        "current_phase": current_phase,
        "difficulty": session["difficulty"],
        "interview_completed": False,
        "report": report
    }

    return {"result": result}


# ---------------------------------------------------------
# NODE 5: RETRIEVE RELEVANT RESUME CONTEXT
# ---------------------------------------------------------



async def retrieve_resume_context(state: VoxHireState):

    session = state["session"]

    resume_context = ""
    resume_id = session.get("resume_id")

    jd_analysis = session.get("jd_analysis") or {}

    # Build a retrieval query using the current question
    # and the job description requirements.
    jd_details = []

    for field in [
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "interview_focus_areas"
    ]:
        values = jd_analysis.get(field, [])

        if isinstance(values, list):
            jd_details.extend(str(value) for value in values)

    retrieval_query = (
        f"{session['current_question']}\n"
        f"{state['answer']}\n"
        f"{' '.join(jd_details)}"
    )

    if resume_id:

        try:

            # Search resume chunks stored in MongoDB
            retrieved_chunks = await search_resume(
                resume_id=resume_id,
                query=retrieval_query,
                owner_id=session.get("candidate_id"),
                top_k=4
            )

            resume_context = "\n\n".join(
                item["text"]
                for item in retrieved_chunks
            )

            print(
                "RESUME CONTEXT RETRIEVED:",
                len(retrieved_chunks)
            )

        except Exception as error:

            print(
                "RESUME CONTEXT RETRIEVAL ERROR:",
                error
            )

    return {"resume_context": resume_context}


# ---------------------------------------------------------
# NODE 6: EVALUATE CANDIDATE ANSWER
# ---------------------------------------------------------
def adjust_difficulty(current_difficulty, score):

    difficulty_levels = [
        "beginner",
        "intermediate",
        "advanced"
    ]

    current_index = difficulty_levels.index(
        current_difficulty
    )

    if score >= 8:
        current_index = min(
            current_index + 1,
            len(difficulty_levels) - 1
        )

    elif score <= 4:
        current_index = max(
            current_index - 1,
            0
        )

    return difficulty_levels[current_index]

def select_priority_skill(session):

    jd_analysis = session.get("jd_analysis") or {}

    required_skills = jd_analysis.get(
        "required_skills", []
    )

    preferred_skills = jd_analysis.get(
        "preferred_skills", []
    )

    covered_skills = {
        skill.casefold()
        for skill in session.get("covered_skills", [])
    }

    # Required skills always receive priority.
    for skill in required_skills:

        if skill.casefold() not in covered_skills:
            return skill

    # Preferred skills are considered after required skills.
    for skill in preferred_skills:

        if skill.casefold() not in covered_skills:
            return skill

    return None

async def evaluate_candidate_answer(state: VoxHireState):

    from app.services.interview_engine import INTERVIEW_PHASES

    session = state["session"]

    phase = INTERVIEW_PHASES[
        session["phase_index"]
    ]

    next_phase_index = session["phase_index"]

    if (
        session["questions_in_phase"] + 1
        >= phase["max_questions"]
    ):
        next_phase_index += 1

    if next_phase_index < len(INTERVIEW_PHASES):

        next_phase = INTERVIEW_PHASES[
            next_phase_index
        ]["name"]

    else:

        next_phase = "Interview completed"

    follow_up_allowed = (
        session["follow_up_count"] == 0
    )

    jd_analysis = session.get("jd_analysis") or {}

    required_skills = jd_analysis.get("required_skills", [])
    preferred_skills = jd_analysis.get("preferred_skills", [])

    all_jd_skills = required_skills + preferred_skills

    covered_skills = session.get("covered_skills", [])

    uncovered_skills = [
        skill
        for skill in all_jd_skills
        if skill.casefold() not in {
            covered.casefold()
            for covered in covered_skills
        }
    ]

    priority_skill = select_priority_skill(session)

    target_difficulty = session["difficulty"]

    asked_questions = session.setdefault(
        "asked_questions",
        [session["current_question"]]
    )
    evaluation = await evaluate_answer(
    role=session["role"],
    difficulty=session["difficulty"],
    phase=phase["name"],
    question=session["current_question"],
    answer=state["answer"],
    next_phase=next_phase,
    follow_up_allowed=follow_up_allowed,
    previous_answers=session["answers"],
    resume_context=state.get("resume_context", ""),
    jd_analysis=jd_analysis,
    interview_mode=session.get("interview_mode", "role"),
    uncovered_skills=uncovered_skills,
    priority_skill=priority_skill,
    asked_questions=asked_questions,
    target_difficulty=target_difficulty
)

    return {
        "evaluation": evaluation,
        "phase": phase,
        "next_phase": next_phase,
        "follow_up_allowed": follow_up_allowed
    }


# ---------------------------------------------------------
# NODE 7: UPDATE SESSION AND GENERATE NEXT QUESTION
# ---------------------------------------------------------

def update_session(state: VoxHireState):

    session = state["session"]
    evaluation = state["evaluation"]
    phase = state["phase"]

    # -------------------------------------------------
    # 1. SAVE THE CANDIDATE'S ANSWER
    # -------------------------------------------------

    record = {
        "phase": phase["name"],
        "question": session["current_question"],
        "answer": state["answer"],
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "strengths": evaluation["strengths"],
        "improvements": evaluation["improvements"]
    }

    session["answers"].append(record)
    session["scores"].append(evaluation["score"])

    # -------------------------------------------------
    # 2. UPDATE JD SKILL COVERAGE
    # -------------------------------------------------

    if session.get("interview_mode") == "job_description":

        covered_skills = session.setdefault(
            "covered_skills", []
        )

        for skill in evaluation.get("skills_assessed", []):

            if skill.casefold() not in {
                item.casefold() for item in covered_skills
            }:
                covered_skills.append(skill)

        print("JD SKILLS ASSESSED:", covered_skills)

    # -------------------------------------------------
    # 3. CHECK WHETHER A FOLLOW-UP IS REQUIRED
    # -------------------------------------------------

    ask_follow_up = (
        evaluation["ask_follow_up"]
        and state["follow_up_allowed"]
    )

    if ask_follow_up:

        session["follow_up_count"] += 1

        # Follow-ups do not count as main questions.
        next_question = evaluation["next_question"]

    else:

        session["follow_up_count"] = 0

        # -------------------------------------------------
        # 4. COUNT MAIN QUESTIONS
        # -------------------------------------------------

        session["main_questions_count"] = (
            session.get("main_questions_count", 0) + 1
        )

        session["questions_in_phase"] += 1

        # -------------------------------------------------
        # 5. ADAPT DIFFICULTY
        # -------------------------------------------------

        session["difficulty"] = adjust_difficulty(
            current_difficulty=session["difficulty"],
            score=evaluation["score"]
        )

        print(
            "ADAPTIVE DIFFICULTY:",
            session["difficulty"]
        )

        # -------------------------------------------------
        # 6. ADVANCE INTERVIEW PHASE
        # -------------------------------------------------

        if (
            session["questions_in_phase"]
            >= phase["max_questions"]
        ):

            if session["phase_index"] < len(INTERVIEW_PHASES) - 1:

                session["phase_index"] += 1

                session["questions_in_phase"] = 0

        # -------------------------------------------------
        # 7. CHECK REMAINING REQUIRED JD SKILLS
        # -------------------------------------------------

        jd_analysis = session.get("jd_analysis") or {}

        required_skills = jd_analysis.get(
            "required_skills", []
        )

        covered_lookup = {
            skill.casefold()
            for skill in session.get("covered_skills", [])
        }

        uncovered_required = [
            skill
            for skill in required_skills
            if skill.casefold() not in covered_lookup
        ]

        # -------------------------------------------------
        # 8. DYNAMIC INTERVIEW LENGTH
        # -------------------------------------------------

        max_questions = session.get(
            "max_main_questions", 10
        )

        total_questions = session["main_questions_count"]

        is_jd_interview = (
            session.get("interview_mode") == "job_description"
        )

        at_last_phase = (
            session["phase_index"] == len(INTERVIEW_PHASES) - 1
        )

        should_extend = (
            is_jd_interview
            and at_last_phase
            and bool(uncovered_required)
            and total_questions < max_questions
        )

        if should_extend:

            # Continue asking questions in Practical Scenarios.
            session["questions_in_phase"] = 0

            print(
                "EXTENDING INTERVIEW FOR UNCOVERED SKILLS:",
                uncovered_required
            )

        # -------------------------------------------------
        # 9. DECIDE WHETHER INTERVIEW IS COMPLETE
        # -------------------------------------------------

        reached_maximum = (
            total_questions >= max_questions
        )

        if reached_maximum:

            session["completed"] = True

        elif (
            session["phase_index"] >= len(INTERVIEW_PHASES) - 1
            and not should_extend
            and session["questions_in_phase"] >=
                INTERVIEW_PHASES[-1]["max_questions"]
        ):

            session["completed"] = True

        # -------------------------------------------------
        # 10. SELECT NEXT QUESTION
        # -------------------------------------------------

        if session["completed"]:

            next_question = (
                "Thank you! You have completed your interview. "
                "Here is your performance summary."
            )

        else:

            next_question = evaluation["next_question"]

    # -------------------------------------------------
    # 11. PREVENT EMPTY QUESTIONS
    # -------------------------------------------------

    if not next_question or not next_question.strip():

        next_question = (
            "Could you explain your approach "
            "with a practical example?"
        )

    # -------------------------------------------------
    # 12. PREVENT EXACT QUESTION REPETITION
    # -------------------------------------------------

    asked_questions = session.setdefault(
        "asked_questions",
        []
    )

    normalized_question = next_question.strip().casefold()

    previous_questions = {
        item.strip().casefold()
        for item in asked_questions
    }

    if (
        not session["completed"]
        and normalized_question in previous_questions
    ):

        priority_skill = select_priority_skill(session)

        if priority_skill:

            next_question = (
                f"Can you explain how you would use "
                f"{priority_skill} to solve a practical "
                f"problem in this role?"
            )

        else:

            next_question = (
                "Can you describe a different practical "
                "scenario related to this role and explain "
                "how you would approach it?"
            )

    # -------------------------------------------------
    # 13. SAVE THE NEXT QUESTION
    # -------------------------------------------------

    session["current_question"] = next_question

    if not session["completed"]:

        asked_questions.append(next_question)

        session["current_target_skill"] = (
            select_priority_skill(session)
        )

    print(
        "NEXT TARGET SKILL:",
        session.get("current_target_skill")
    )

    print(
        "TOTAL MAIN QUESTIONS:",
        session.get("main_questions_count", 0)
    )

    # -------------------------------------------------
    # 14. GENERATE REPORT IF COMPLETED
    # -------------------------------------------------

    report = None

    if session["completed"]:

        report = state["report_generator"](session)

    # -------------------------------------------------
    # 15. RETURN RESULT TO FRONTEND
    # -------------------------------------------------

    result = {
        "session_id": state["session_id"],
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

    return {"result": result}

# ---------------------------------------------------------
# BUILD THE ACTUAL VOXHIRE GRAPH
# ---------------------------------------------------------

workflow_builder = StateGraph(VoxHireState)

workflow_builder.add_node("load_session", load_session)

workflow_builder.add_node(
    "handle_pending_confirmation",
    handle_pending_confirmation
)

workflow_builder.add_node(
    "detect_intent",
    detect_intent_node
)

workflow_builder.add_node(
    "handle_non_answer",
    handle_non_answer
)

workflow_builder.add_node(
    "retrieve_resume_context",
    retrieve_resume_context
)

workflow_builder.add_node(
    "evaluate_answer",
    evaluate_candidate_answer
)

workflow_builder.add_node(
    "update_session",
    update_session
)


workflow_builder.add_edge(START, "load_session")


workflow_builder.add_conditional_edges(
    "load_session",
    route_after_load,
    {
        "pending": "handle_pending_confirmation",
        "intent": "detect_intent"
    }
)


workflow_builder.add_edge(
    "handle_pending_confirmation",
    END
)


workflow_builder.add_conditional_edges(
    "detect_intent",
    route_after_intent,
    {
        "answer": "retrieve_resume_context",
        "non_answer": "handle_non_answer"
    }
)


workflow_builder.add_edge(
    "handle_non_answer",
    END
)


workflow_builder.add_edge(
    "retrieve_resume_context",
    "evaluate_answer"
)


workflow_builder.add_edge(
    "evaluate_answer",
    "update_session"
)


workflow_builder.add_edge(
    "update_session",
    END
)


voxhire_interview_graph = workflow_builder.compile()


# ---------------------------------------------------------
# FUNCTION CALLED BY INTERVIEW_ENGINE.PY
# ---------------------------------------------------------

async def run_interview_workflow(
    session_id: str,
    answer: str,
    session_store: dict,
    report_generator: Callable
):

    initial_state = {
        "session_id": session_id,
        "answer": answer,
        "session_store": session_store,
        "report_generator": report_generator
    }

    result = await voxhire_interview_graph.ainvoke(
        initial_state
    )

    return result["result"]
