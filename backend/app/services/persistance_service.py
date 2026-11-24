
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import get_database


async def save_interview(
    candidate_id: str,
    session_id: str,
    role: str,
    difficulty: str,
    report: dict
):
    db = get_database()

    document = {
        "candidate_id": candidate_id,
        "session_id": session_id,
        "role": role,
        "difficulty": difficulty,
        "report": report,
        "created_at": datetime.now(timezone.utc)
    }

    result = await db.interviews.insert_one(document)

    return str(result.inserted_id)


async def get_interview_history(candidate_id: str):
    db = get_database()

    cursor = db.interviews.find(
        {"candidate_id": candidate_id}
    ).sort("created_at", -1)

    interviews = []

    async for item in cursor:
        item["_id"] = str(item["_id"])
        interviews.append(item)

    return interviews



async def get_interview_by_id(interview_id: str, candidate_id: str):
    db = get_database()

    if not ObjectId.is_valid(interview_id):
        return None

    interview = await db.interviews.find_one({
        "_id": ObjectId(interview_id),
        "candidate_id": candidate_id
    })

    if interview:
        interview["_id"] = str(interview["_id"])

    return interview



async def get_dashboard_summary(candidate_id: str):
    interviews = await get_interview_history(candidate_id)

    if not interviews:
        return {
            "total_interviews": 0,
            "overall_score": 0,
            "latest_interview": None,
            "skill_coverage": 0
        }

    scores = []
    coverage_values = []

    for interview in interviews:
        report = interview.get("report", {})

        score = report.get("overall_score")

        if score is not None:
            scores.append(float(score))

        coverage = report.get("skill_coverage", {})
        percentage = coverage.get("required_coverage_percentage")

        if percentage is not None:
            coverage_values.append(float(percentage))

    average_score = (
        round(sum(scores) / len(scores), 2)
        if scores else 0
    )

    skill_coverage = (
        round(sum(coverage_values) / len(coverage_values), 2)
        if coverage_values else 0
    )

    latest = interviews[0]

    return {
        "total_interviews": len(interviews),
        "overall_score": average_score,
        "skill_coverage": skill_coverage,
        "latest_interview": {
            "role": latest.get("role"),
            "difficulty": latest.get("difficulty"),
            "created_at": latest.get("created_at")
        }
    }
