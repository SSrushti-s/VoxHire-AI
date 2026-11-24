
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.resume_service import extract_resume_text
from app.services.resume_analyzer import analyze_resume
from app.services.retrieval_service import (
    build_resume_index,
    search_resume
)


router = APIRouter(
    prefix="/api/resume",
    tags=["Resume Intelligence"]
)


class ResumeSearchRequest(BaseModel):
    resume_id: str
    query: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):

    user_id = str(current_user["_id"])

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB."
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )

    try:
        result = extract_resume_text(pdf_bytes)

        candidate_profile = await analyze_resume(
            result["extracted_text"]
        )

        index_result = build_resume_index(
            result["extracted_text"],
            owner_id=user_id
        )

        return {
            "success": True,
            "message": "Resume uploaded and analyzed successfully.",
            "filename": file.filename,
            "page_count": result["page_count"],
            "character_count": result["character_count"],
            "resume_id": index_result["resume_id"],
            "indexed_chunks": index_result["chunk_count"],
            "candidate_profile": candidate_profile
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    finally:
        await file.close()


@router.post("/search")
async def search_resume_endpoint(
    request: ResumeSearchRequest,
    current_user: dict = Depends(get_current_user)
):

    user_id = str(current_user["_id"])

    try:
        results = search_resume(
            resume_id=request.resume_id,
            query=request.query,
            top_k=request.top_k,
            owner_id=user_id
        )

        return {
            "success": True,
            "query": request.query,
            "results_count": len(results),
            "retrieved_chunks": results
        }

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload it again."
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Resume not found."
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print("RESUME SEARCH ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail="Unable to search resume."
        )
