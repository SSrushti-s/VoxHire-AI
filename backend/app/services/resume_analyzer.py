
import json

from groq import AsyncGroq
from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


async def analyze_resume(resume_text: str):

    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is empty.")

    # Limit input size to avoid excessively large LLM requests
    resume_text = resume_text[:20000]

    system_prompt = """
You are VoxHire, an expert AI resume analyzer.

Analyze the candidate's resume and extract information accurately.

Return ONLY a valid JSON object with this exact structure:

{
    "candidate_name": "",
    "email": "",
    "phone": "",
    "summary": "",
    "skills": {
        "programming_languages": [],
        "frameworks": [],
        "tools": [],
        "ai_ml_skills": [],
        "databases": []
    },
    "education": [
        {
            "degree": "",
            "institution": "",
            "year": ""
        }
    ],
    "experience": [
        {
            "role": "",
            "company": "",
            "duration": "",
            "description": ""
        }
    ],
    "projects": [
        {
            "name": "",
            "description": "",
            "technologies": [],
            "domain": ""
        }
    ],
    "certifications": []
}

IMPORTANT RULES:

1. Extract only information explicitly present in the resume.
2. Never invent candidate details, skills, experience or projects.
3. Use empty strings when information is unavailable.
4. Use empty arrays when a section has no information.
5. Keep descriptions concise but meaningful.
6. Separate programming languages, frameworks, tools,
   AI/ML skills and databases correctly.
7. Preserve project names and technologies accurately.
8. Return valid JSON only. No Markdown or explanations.
"""

    try:
        completion = await client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Analyze this resume:\n\n{resume_text}"
                }
            ],
            temperature=0.1,
            max_completion_tokens=2000,
            response_format={"type": "json_object"}
        )

        raw_response = completion.choices[0].message.content

        if not raw_response:
            raise ValueError("The AI returned an empty response.")

        profile = json.loads(raw_response)

        # Basic validation of the returned structure
        required_fields = [
            "candidate_name",
            "email",
            "phone",
            "summary",
            "skills",
            "education",
            "experience",
            "projects",
            "certifications"
        ]

        for field in required_fields:
            if field not in profile:
                raise ValueError(
                    f"AI response is missing the field: {field}"
                )

        print("RESUME ANALYSIS COMPLETED")

        return profile

    except json.JSONDecodeError as error:
        print("RESUME JSON PARSING ERROR:", error)
        raise ValueError("Unable to process the AI analysis response.")

    except Exception as error:
        print("RESUME ANALYSIS ERROR:", error)
        raise
