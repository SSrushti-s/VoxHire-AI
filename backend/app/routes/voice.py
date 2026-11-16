
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from app.services.stt_service import transcribe_audio
from app.services.tts_service import generate_speech

router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        audio = await file.read()

        if not audio:
            raise HTTPException(
                status_code=400,
                detail="Empty audio recording"
            )

        if len(audio) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio file is too large"
            )

        transcript = await transcribe_audio(
            audio,
            file.filename or "recording.webm"
        )

        return {"transcript": transcript}

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(error)}"
        )


@router.post("/speak")
async def speak(payload: dict):
    try:
        text = payload.get("text", "").strip()

        if not text or len(text) > 3000:
            raise HTTPException(
                status_code=400,
                detail="Text must contain 1-3000 characters"
            )

        audio = await generate_speech(text)

        return Response(
            content=audio,
            media_type="audio/mpeg"
        )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Speech generation failed: {str(error)}"
        )
