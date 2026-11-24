
import json

from groq import AsyncGroq

from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL


client = AsyncGroq(api_key=GROQ_API_KEY)


async def analyze_job_description(job_description: str):

    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    job_description = job_description.strip()

    if len(job_description) > 15000:
        raise ValueError("Job description must be under 15,000 characters.")

    prompt = f"""
You are an expert technical recruitment analyst.

Analyze the following job description.

Extract:
1. Job title
2. Seniority level
3. Required technical skills
4. Preferred technical skills
5. Responsibilities
6. Required qualifications
7. Important interview focus areas

Do not invent requirements that are not supported by the job description.

Return valid JSON in this structure:

{{
    "job_title": "Job title",
    "seniority": "Junior, Mid-level or Senior",
    "required_skills": [],
    "preferred_skills": [],
    "responsibilities": [],
    "qualifications": [],
    "interview_focus_areas": []
}}

JOB DESCRIPTION:

{job_description}
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
            temperature=0.1,
            max_completion_tokens=1200,
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content

        if not content:
            raise ValueError("Empty JD analysis response.")

        result = json.loads(content)

        required_fields = [
            "job_title",
            "seniority",
            "required_skills",
            "preferred_skills",
            "responsibilities",
            "qualifications",
            "interview_focus_areas"
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    f"Missing field in JD analysis: {field}"
                )

        print("JOB DESCRIPTION ANALYSIS:", result)

        return result

    except Exception as error:
        print("JD ANALYSIS ERROR:", error)
        raise
