
const API_URL = "http://localhost:8000";

// Start a new interview
export async function startInterview(role, difficulty) {

    const response = await fetch(`${API_URL}/api/interview/start`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            role,
            difficulty
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Could not start interview");
    }

    return response.json();
}


// Submit a candidate answer
export async function submitAnswer(sessionId, message) {

    const response = await fetch(`${API_URL}/api/interview/respond`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            session_id: sessionId,
            message
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Could not submit answer");
    }

    return response.json();
}


// Get final interview report
export async function getInterviewReport(sessionId) {

    const response = await fetch(
        `${API_URL}/api/interview/report/${sessionId}`
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Could not fetch report");
    }

    return response.json();
}


// Convert microphone recording into text
export async function transcribeAudio(audioBlob) {

    const formData = new FormData();

    formData.append("file", audioBlob, "recording.webm");

    const response = await fetch(
        `${API_URL}/api/voice/transcribe`,
        {
            method: "POST",
            body: formData
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Transcription failed");
    }

    return response.json();
}
