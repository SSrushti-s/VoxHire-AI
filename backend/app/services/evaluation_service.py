
import json

from groq import AsyncGroq
from app.core.config import GROQ_API_KEY, GROQ_CHAT_MODEL

client = AsyncGroq(api_key=GROQ_API_KEY)


async def evaluate_answer(
    role,
    difficulty,
    phase,
    question,
    answer,
    next_phase,
    follow_up_allowed,
    previous_answers,
    resume_context="",
    jd_analysis=None,
    interview_mode="role",
    uncovered_skills=None,
    priority_skill=None,
    asked_questions=None,
    target_difficulty=None
):
    jd_analysis = jd_analysis or {}

    uncovered_skills = uncovered_skills or []
    system_prompt = f"""
You are VoxHire, a professional technical interviewer
and evaluator.

Your task is to evaluate the candidate's answer and
generate the next appropriate interview question.

Return ONLY a valid JSON object with these fields:

{{
    "score": 0,
    "feedback": "Short conversational feedback",
    "strengths": ["strength 1"],
    "improvements": ["improvement 1"],
    "ask_follow_up": false,
    "next_question": "The next interview question",
    "next_difficulty": "intermediate",
    "skills_assessed": ["React", "JavaScript"]
}}

GENERAL EVALUATION RULES:

1. Score the answer from 0 to 10.
2. Evaluate technical correctness, clarity and completeness.
3. Do not give a high score for an incorrect or irrelevant answer.
4. Give constructive and specific feedback.
5. If the answer is incomplete or unclear, consider asking a follow-up.
6. Ask at most one follow-up for each main question.
7. If a follow-up is not allowed, continue to the next question.
8. Adjust difficulty according to candidate performance.
9. Use only these difficulty values:
   beginner, intermediate, advanced.
10. The next question must match the intended next phase.
11. If a follow-up is required, ask about the current question.
12. Keep feedback and questions conversational and suitable for voice.
13. Do not reveal the complete expected answer.
14. Never output Markdown fences or text outside JSON.
15. The next question must be a complete grammatical question.
16. End every interview question with a question mark.
17. Do not generate half-finished questions.

RESUME-AWARE EVALUATION:

1. Treat resume information as supporting context, not proof.
2. Never assume the candidate personally implemented every
   project or feature listed in the resume.
3. Do not penalize an answer merely because it does not
   repeat information from the resume.
4. Use retrieved resume information only when relevant.
5. If the candidate mentions a project, explore their
   implementation, decisions, challenges and contributions.
6. Never invent candidate experience or skills.

JOB DESCRIPTION-AWARE EVALUATION:

Interview mode:
{interview_mode}

Job title:
{jd_analysis.get("job_title", role)}

Seniority:
{jd_analysis.get("seniority", "Not specified")}

Required skills:
{jd_analysis.get("required_skills", [])}

Preferred skills:
{jd_analysis.get("preferred_skills", [])}

Responsibilities:
{jd_analysis.get("responsibilities", [])}

Qualifications:
{jd_analysis.get("qualifications", [])}

Interview focus areas:
{jd_analysis.get("interview_focus_areas", [])}

Rules for JD-based interviews:

1. When interview mode is job_description, use the supplied
   JD as the main source for interview requirements.

2. Prioritize required skills over preferred skills.

3. Generate questions relevant to the actual responsibilities
   and interview focus areas.

4. Do not ask questions about technologies or requirements
   that are not supported by the JD.

5. Use the candidate's previous answers to identify topics
   that have already been adequately covered.

6. Prefer exploring a new required skill or responsibility
   instead of repeatedly asking about the same topic.

7. If the candidate performs well, increase the complexity
   of the next question when appropriate.

8. If the candidate struggles, simplify the next question
   or explore the underlying fundamentals.

9. If a follow-up is needed, ask about the current question
   rather than introducing an unrelated topic.

10. If interview mode is role, continue evaluating according
    to the selected job role.

11. Return the exact names of the JD skills that the current
    question and candidate's answer actually assessed.

12. Only select skills from the supplied required_skills
    and preferred_skills lists.

13. Do not mark a skill as assessed merely because it was
    mentioned in the question. The question must meaningfully
    test that skill.

14. If the answer does not demonstrate or test a particular
    skill, do not include it.

15. Use uncovered_skills to prioritize the next question
    when moving to a new question.

16. Never claim that a skill is fully mastered just because
    it was assessed once.

QUESTION GENERATION:

- If a follow-up is needed, generate one focused follow-up.
- Otherwise, generate a question for the next interview phase.
- Make the question relevant to the selected difficulty.
- Avoid repeating previous questions.
- Ask only one question at a time.
- Keep the question between approximately 15 and 60 words.
- Return a complete question ending with '?'.

ADAPTIVE INTERVIEW RULES:

1. The target difficulty for the next question is:
{target_difficulty or difficulty}

2. If a priority skill is provided, the next main
   question should meaningfully assess that skill.

3. Do not choose a skill that has already been assessed
   if an uncovered required skill is available.

4. Previous questions are provided in the context.
   Do not repeat or slightly rephrase them.

5. Ask a different question that tests a new concept,
   implementation decision, or practical scenario.

6. If a follow-up is needed, it must remain focused
   on the current question and must not introduce
   an unrelated skill.

7. Never invent skills outside the supplied job description.
"""

    context = {
        "role": role,
        "interview_mode": interview_mode,
        "current_difficulty": difficulty,
        "current_phase": phase,
        "current_question": question,
        "candidate_answer": answer,
        "next_phase_if_continuing": next_phase,
        "follow_up_allowed": follow_up_allowed,
        "previous_answers": previous_answers[-6:],
        "resume_context": resume_context,
        "job_description_analysis": jd_analysis,
        "uncovered_skills": uncovered_skills,
        "priority_skill": priority_skill,
        "target_difficulty": target_difficulty or difficulty,
        "asked_questions": (asked_questions or [])[-10:],
    }

    completion = await client.chat.completions.create(
        model=GROQ_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False)
            }
        ],
        temperature=0.4,
        max_completion_tokens=1800,
        response_format={"type": "json_object"}
    )

    raw_response = completion.choices[0].message.content

    if not raw_response:
        raise ValueError("Empty evaluation response from AI.")

    result = json.loads(raw_response)

    score = int(result.get("score", 0))
    score = max(0, min(score, 10))

    difficulty_value = result.get(
        "next_difficulty",
        difficulty
    )

    if difficulty_value not in (
        "beginner",
        "intermediate",
        "advanced"
    ):
        difficulty_value = difficulty

    strengths = result.get("strengths", [])
    improvements = result.get("improvements", [])

    next_question = str(
        result.get("next_question", "")
    ).strip()

    # Only accept skills that actually exist in the JD.
    allowed_skills = (
        jd_analysis.get("required_skills", [])
        + jd_analysis.get("preferred_skills", [])
    )

    allowed_skill_map = {
        str(skill).strip().casefold(): str(skill).strip()
        for skill in allowed_skills
    }

    raw_assessed_skills = result.get("skills_assessed", [])

    if not isinstance(raw_assessed_skills, list):
        raw_assessed_skills = []

    skills_assessed = []

    for skill in raw_assessed_skills:
        normalized_skill = str(skill).strip().casefold()

        if normalized_skill in allowed_skill_map:
            canonical_skill = allowed_skill_map[normalized_skill]

            if canonical_skill not in skills_assessed:
                skills_assessed.append(canonical_skill)
    if not next_question:
        raise ValueError("AI did not generate the next interview question.")

    if not next_question.endswith(("?", ".", "!")):
        raise ValueError("AI generated an incomplete interview question.")

    return {
        "score": score,
        "feedback": str(
            result.get("feedback", "Answer evaluated.")
        ),
        "strengths": strengths if isinstance(strengths, list) else [],
        "improvements": improvements if isinstance(improvements, list) else [],
        "ask_follow_up": bool(result.get("ask_follow_up", False)),
        "next_question": next_question,
        "next_difficulty": difficulty_value,
        "skills_assessed": skills_assessed
    }
