
import re

from groq import AsyncGroq
from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


def detect_simple_intent(message: str):
    """
    Detect common interview commands using Python.
    This avoids unnecessary LLM calls for obvious requests.
    """

    text = message.lower().strip()

    # Candidate wants help answering the question
    if re.search(r"\b(hint|clue|tip)\b", text) or any(
        phrase in text for phrase in [
            "help me answer",
            "help answering",
            "give me guidance",
            "guide me"
        ]
    ):
        return "HINT"

    # Candidate wants the question repeated
    if any(phrase in text for phrase in [
        "repeat",
        "say that again",
        "ask the question again",
        "could you say that again"
    ]):
        return "REPEAT"

    # Candidate wants clarification
    if any(phrase in text for phrase in [
        "clarify",
        "explain the question",
        "what do you mean",
        "i don't understand the question"
    ]):
        return "CLARIFY"

    # Candidate requests a report or score
    if re.search(r"\b(report|score summary|performance summary)\b", text):
        return "REPORT_REQUEST"

    # Candidate wants to end the interview
    if any(phrase in text for phrase in [
        "end interview",
        "stop interview",
        "finish interview",
        "quit interview",
        "i want to stop",
        "i want to end"
    ]):
        return "END_INTERVIEW"

    return None


async def detect_intent(message: str):
    # Step 1: Check obvious intents locally
    simple_intent = detect_simple_intent(message)

    if simple_intent:
        print("INTENT DETECTED LOCALLY:", simple_intent)
        return simple_intent

    # Step 2: Use Groq for messages that need interpretation
    prompt = f"""
You are an intent classifier for an AI interview application.

Classify the candidate's message into exactly one category:

ANSWER
REPEAT
CLARIFY
HINT
REPORT_REQUEST
END_INTERVIEW
OTHER

Rules:
- ANSWER: Candidate is attempting to answer the interview question.
- REPEAT: Candidate wants the question repeated.
- CLARIFY: Candidate wants the question explained.
- HINT: Candidate requests a hint or help answering.
- REPORT_REQUEST: Candidate requests their interview report or score.
- END_INTERVIEW: Candidate explicitly wants to stop the interview.
- OTHER: General conversation or unrelated request.

Examples:
"Can you give me a hint?" -> HINT
"I need a clue" -> HINT
"Can you repeat the question?" -> REPEAT
"What exactly do you mean?" -> CLARIFY
"Show me my report" -> REPORT_REQUEST
"I want to stop the interview" -> END_INTERVIEW
"React uses components to build user interfaces" -> ANSWER

Return ONLY the category name.

Candidate message:
{message}
"""

    allowed = {
        "ANSWER",
        "REPEAT",
        "CLARIFY",
        "HINT",
        "REPORT_REQUEST",
        "END_INTERVIEW",
        "OTHER"
    }

    try:
        completion = await client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=256
        )

        raw_result = completion.choices[0].message.content or ""
        result = raw_result.strip().upper()

        print("INTENT RAW RESPONSE:", repr(result))

        # Extract a valid category even if the model adds extra text
        for category in allowed:
            if re.search(
                rf"(?<![A-Z]){re.escape(category)}(?![A-Z])",
                result
            ):
                print("INTENT DETECTED:", category)
                return category

        # If the classifier returns nothing, treat the message as an answer.
        print("Could not classify intent. Defaulting to ANSWER.")
        return "ANSWER"

    except Exception as error:
        print("INTENT CLASSIFICATION ERROR:", error)
        return "ANSWER"
