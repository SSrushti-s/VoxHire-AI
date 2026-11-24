
import uuid

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Load the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# In-memory resume index storage
resume_indexes = {}


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


def build_resume_index(text: str, owner_id: str):
    if not text or not text.strip():
        raise ValueError("Resume text is empty.")

    chunks = split_text(text)

    if not chunks:
        raise ValueError("No usable text found in resume.")

    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    resume_id = str(uuid.uuid4())

    resume_indexes[resume_id] = {
        "index": index,
        "chunks": chunks,
        "owner_id": owner_id
    }

    return {
        "resume_id": resume_id,
        "chunk_count": len(chunks)
    }


def search_resume(
    resume_id: str,
    query: str,
    top_k: int = 3,
    owner_id: str = None
):
    if resume_id not in resume_indexes:
        raise KeyError("Resume index not found.")

    resume_data = resume_indexes[resume_id]

    # Check ownership before searching
    if not owner_id or resume_data.get("owner_id") != owner_id:
        raise PermissionError("You cannot access this resume.")

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    index = resume_data["index"]
    chunks = resume_data["chunks"]

    search_count = min(top_k, len(chunks))

    scores, indices = index.search(
        query_embedding,
        search_count
    )

    results = []

    for score, chunk_index in zip(scores[0], indices[0]):

        if chunk_index < 0:
            continue

        results.append({
            "chunk_id": int(chunk_index),
            "similarity_score": float(score),
            "text": chunks[chunk_index]
        })

    return results
