
import json

from groq import AsyncGroq
from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


async def evaluate_answer(
    role: str,
    difficulty: str,
    phase: str,
    question: str,
    answer: str,
    next_phase: str,
    follow_up_allowed: bool,
    previous_answers: list
):
    system_prompt = """
You are VoxHire, a professional technical interviewer and evaluator.

Evaluate the candidate's answer fairly.

Return ONLY a valid JSON object with these fields:

{
    "score": 0,
    "feedback": "Short conversational feedback",
    "strengths": ["strength 1"],
    "improvements": ["improvement 1"],
    "ask_follow_up": false,
    "next_question": "The next interview question",
    "next_difficulty": "intermediate"
}

Rules:

1. Score the answer from 0 to 10.
2. Evaluate technical correctness, clarity and completeness.
3. Do not give a high score for an incorrect or irrelevant answer.
4. Give constructive and specific feedback.
5. If the answer is incomplete or unclear, consider asking a follow-up.
6. Ask at most one follow-up for each main question.
7. If a follow-up is not allowed, continue to the next question.
8. Keep questions relevant to the selected job role.
9. Adjust difficulty according to candidate performance.
10. Use only these difficulty values:
    beginner, intermediate, advanced.
11. The next question must match the intended next phase.
12. If a follow-up is required, ask about the current question.
13. Keep feedback and questions suitable for spoken conversation.
14. Do not reveal the complete expected answer.
15. Never output Markdown fences or additional text outside JSON.
"""

    context = {
        "role": role,
        "current_difficulty": difficulty,
        "current_phase": phase,
        "current_question": question,
        "candidate_answer": answer,
        "next_phase_if_continuing": next_phase,
        "follow_up_allowed": follow_up_allowed,
        "previous_answers": previous_answers[-6:]
    }

    completion = await client.chat.completions.create(
        model=GROQ_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(context)
            }
        ],
        temperature=0.4,
        max_completion_tokens=700,
        response_format={"type": "json_object"}
    )

    raw_response = completion.choices[0].message.content

    result = json.loads(raw_response)

    score = int(result.get("score", 0))
    score = max(0, min(score, 10))

    difficulty_value = result.get(
        "next_difficulty", difficulty
    )

    if difficulty_value not in (
        "beginner", "intermediate", "advanced"
    ):
        difficulty_value = difficulty

    strengths = result.get("strengths", [])
    improvements = result.get("improvements", [])

    return {
        "score": score,
        "feedback": str(result.get("feedback", "Answer evaluated.")),
        "strengths": strengths if isinstance(strengths, list) else [],
        "improvements": improvements if isinstance(improvements, list) else [],
        "ask_follow_up": bool(result.get("ask_follow_up", False)),
        "next_question": str(result.get("next_question", "")).strip(),
        "next_difficulty": difficulty_value
    }
