
from groq import AsyncGroq

from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


async def generate_personalized_question(
    role: str,
    difficulty: str,
    resume_context: str
):
    """
    Generate an interview question using relevant resume context.
    """

    prompt = f"""
You are VoxHire, an intelligent technical interviewer.

Generate ONE personalized opening interview question.

Candidate's selected role:
{role}

Interview difficulty:
{difficulty}

Relevant information extracted from the candidate's resume:
{resume_context}

Instructions:
1. Ask about an actual project, skill or experience mentioned in the resume.
2. Make the question relevant to the selected job role.
3. Prefer questions that allow the candidate to explain their
   implementation, decisions and technical contributions.
4. Do not invent projects or technologies.
5. Do not ask multiple questions at once.
6. Keep the question conversational and suitable for voice.
7. Do not provide the answer or any hints.

Return ONLY the interview question.
"""

    try:
        completion = await client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_completion_tokens=400
        )

        question = completion.choices[0].message.content

        if not question or not question.strip():
            raise ValueError("Empty question generated.")

        return question.strip()

    except Exception as error:
        print("PERSONALIZED QUESTION ERROR:", error)
        raise
