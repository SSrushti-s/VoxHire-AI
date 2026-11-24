
from groq import AsyncGroq

from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL


client = AsyncGroq(api_key=GROQ_API_KEY)


async def generate_jd_opening_question(
    difficulty: str,
    jd_analysis: dict,
    resume_context: str = ""
):

    prompt = f"""
You are VoxHire, an intelligent technical interviewer.

Generate ONE opening interview question.

JOB TITLE:
{jd_analysis.get("job_title", "Technical Position")}

DIFFICULTY:
{difficulty}

REQUIRED SKILLS:
{jd_analysis.get("required_skills", [])}

PREFERRED SKILLS:
{jd_analysis.get("preferred_skills", [])}

RESPONSIBILITIES:
{jd_analysis.get("responsibilities", [])}

INTERVIEW FOCUS AREAS:
{jd_analysis.get("interview_focus_areas", [])}

CANDIDATE RESUME CONTEXT:
{resume_context or "No resume information provided."}

Instructions:
1. Ask one question relevant to the job description.
2. Personalize it using the resume when relevant information is available.
3. Do not invent candidate experience.
4. Match the selected difficulty.
5. Keep it conversational and suitable for voice.
6. Ask only ONE question.
7. Make sure the question is a complete sentence.
8. End with a question mark.

Return only the question.
"""

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
        raise ValueError("Could not generate JD-based opening question.")

    return question.strip()
