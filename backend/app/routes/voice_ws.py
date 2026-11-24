
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.core.security import get_user_from_token
from app.services.stt_service import transcribe_audio
from app.services.interview_engine import process_answer, sessions


router = APIRouter()


@router.websocket("/ws/{session_id}")
async def voice_interview(websocket: WebSocket, session_id: str):

    await websocket.accept()

    try:
        # STEP 1: Receive authentication message
        try:
            auth_message = await websocket.receive_text()
            auth_data = json.loads(auth_message)

            if auth_data.get("type") != "authenticate":
                await websocket.close(code=1008)
                return

            token = auth_data.get("token")

            if not token:
                await websocket.close(code=1008)
                return

        except Exception:
            await websocket.close(code=1008)
            return

        # STEP 2: Verify JWT
        user = await get_user_from_token(token)

        if not user:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed. Please log in."
            })
            await websocket.close(code=1008)
            return

        user_id = str(user["_id"])

        # STEP 3: Verify interview ownership
        session = sessions.get(session_id)

        if not session or session.get("candidate_id") != user_id:
            await websocket.send_json({
                "type": "error",
                "message": "Interview session not found."
            })
            await websocket.close(code=1008)
            return

        # Authentication successful
        await websocket.send_json({
            "type": "authenticated"
        })

        # STEP 4: Receive audio and process interview
        while True:

            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            audio_bytes = message.get("bytes")

            if not audio_bytes:
                await websocket.send_json({
                    "type": "error",
                    "message": "No audio received."
                })
                continue

            # Convert speech into text
            try:
                transcript = await transcribe_audio(
                    audio_bytes,
                    "recording.webm"
                )

            except Exception as error:
                print("TRANSCRIPTION ERROR:", error)

                await websocket.send_json({
                    "type": "error",
                    "message": "Transcription failed."
                })
                continue

            if not transcript:
                await websocket.send_json({
                    "type": "error",
                    "message": "Could not recognize speech."
                })
                continue

            # Process answer
            try:
                result = await process_answer(
                    session_id=session_id,
                    answer=transcript
                )

            except Exception as error:
                print("INTERVIEW PROCESSING ERROR:", error)

                await websocket.send_json({
                    "type": "error",
                    "message": "Interview processing failed."
                })
                continue

            # Return response
            await websocket.send_json({
                "type": "interview_response",
                "transcript": transcript,
                "result": jsonable_encoder(result)
            })

    except WebSocketDisconnect:
        print(f"Voice session disconnected: {session_id}")

    except Exception as error:
        print("WEBSOCKET ERROR:", error)

        try:
            await websocket.close(code=1011)
        except Exception:
            pass
