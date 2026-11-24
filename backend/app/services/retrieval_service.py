
import uuid
import re

from app.core.database import get_database


COLLECTION_NAME = "resume_chunks"


def split_text(text, chunk_size=500, overlap=80):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


async def get_resume_collection():
    db = get_database()
    collection = db[COLLECTION_NAME]

    # Create the text index if it does not already exist.
    await collection.create_index(
        [("text", "text")],
        name="resume_text_index"
    )

    return collection


async def build_resume_index(text: str, owner_id: str):
    if not text or not text.strip():
        raise ValueError("Resume text is empty.")

    if not owner_id:
        raise ValueError("Resume owner is required.")

    chunks = split_text(text)

    if not chunks:
        raise ValueError("No usable text found in resume.")

    collection = await get_resume_collection()

    resume_id = str(uuid.uuid4())

    documents = [
        {
            "resume_id": resume_id,
            "owner_id": owner_id,
            "chunk_id": chunk_id,
            "text": chunk
        }
        for chunk_id, chunk in enumerate(chunks)
    ]

    await collection.insert_many(documents)

    return {
        "resume_id": resume_id,
        "chunk_count": len(chunks)
    }


async def search_resume(
    resume_id: str,
    query: str,
    top_k: int = 3,
    owner_id: str = None
):
    if not resume_id:
        raise ValueError("Resume ID is required.")

    if not owner_id:
        raise PermissionError("Resume owner is required.")

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = await get_resume_collection()

    # Verify that this resume exists and belongs to the user.
    resume = await collection.find_one({
        "resume_id": resume_id
    })

    if not resume:
        raise KeyError("Resume index not found.")

    if resume.get("owner_id") != owner_id:
        raise PermissionError("You cannot access this resume.")

    # Remove punctuation that can interfere with text search.
    terms = re.findall(r"[A-Za-z0-9]+", query)

    if not terms:
        raise ValueError("Search query has no searchable words.")

    search_query = " ".join(terms)

    # Search only this user's resume chunks.
    cursor = collection.find(
        {
            "resume_id": resume_id,
            "owner_id": owner_id,
            "$text": {
                "$search": search_query
            }
        },
        {
            "_id": 0,
            "chunk_id": 1,
            "text": 1,
            "score": {
                "$meta": "textScore"
            }
        }
    ).sort(
        [("score", {"$meta": "textScore"})]
    ).limit(top_k)

    documents = await cursor.to_list(length=top_k)

    results = []

    for document in documents:
        results.append({
            "chunk_id": document["chunk_id"],
            # Kept for compatibility with the previous response shape.
            # This is now a MongoDB text relevance score, not cosine similarity.
            "similarity_score": float(document.get("score", 0)),
            "text": document["text"]
        })

    return results
