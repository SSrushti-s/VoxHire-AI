
from groq import AsyncGroq

from app.core.config import (
    GROQ_API_KEY,
    GROQ_CHAT_MODEL
)

client = AsyncGroq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are VoxHire, an intelligent and friendly AI interviewer.

Your job is to conduct realistic technical and HR interviews.

Rules:

1. Ask one question at a time.
2. Listen carefully to the candidate's answer.
3. Evaluate the answer for correctness and clarity.
4. If the answer is incomplete, ask a helpful follow-up.
5. If the answer is correct, acknowledge it and move forward.
6. Adapt the difficulty based on the candidate's performance.
7. Do not reveal the expected answer immediately.
8. Keep responses conversational and suitable for speech.
9. Avoid unnecessary markdown, tables and long lists.
10. Be encouraging but provide honest feedback.

You are conducting a real interview, not just answering random questions.
"""


async def generate_response(
    message: str,
    history: list,
    interview_role: str
):
    """
    Generates a context-aware interview response
    based on the selected job role.
    """

    # Add the selected role to the system instructions
    system_prompt = SYSTEM_PROMPT + f"""

The candidate is interviewing for the following role:

{interview_role}

IMPORTANT:
- Ask questions relevant to this job role.
- Evaluate technical answers according to this role.
- Adjust question difficulty based on performance.
- Keep the conversation focused on this role.
- Ask relevant follow-up questions.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Add previous conversation messages
    for item in history[-12:]:

        if item["role"] in ("user", "assistant"):

            messages.append({
                "role": item["role"],
                "content": item["content"]
            })

    # Add the latest candidate message
    messages.append({
        "role": "user",
        "content": message
    })

    # Send conversation to Groq
    completion = await client.chat.completions.create(
        model=GROQ_CHAT_MODEL,
        messages=messages,
        temperature=0.6,
        max_completion_tokens=300
    )

    return completion.choices[0].message.content.strip()
