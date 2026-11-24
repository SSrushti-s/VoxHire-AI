
const API_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function saveToken(token) {
    sessionStorage.setItem("access_token", token);
}

export function getToken() {
    return sessionStorage.getItem("access_token");
}

export function logout() {
    sessionStorage.removeItem("access_token");
}


// Common authenticated API helper
export async function apiRequest(endpoint, options = {}) {
    const token = getToken();

    const headers = {
        ...options.headers
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    // Do not set Content-Type manually for FormData.
    if (!(options.body instanceof FormData) && options.body !== undefined) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (response.status === 401) {
        logout();
        throw new Error("Your session has expired. Please log in again.");
    }

    if (!response.ok) {
        throw new Error(data.detail || "Request failed.");
    }

    return data;
}


// Authentication
export async function signupUser(name, email, password) {
    const data = await apiRequest("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify({ name, email, password })
    });

    saveToken(data.access_token);

    return data;
}

export async function loginUser(email, password) {
    const data = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
    });

    saveToken(data.access_token);

    return data;
}

export async function getCurrentUser() {
    return apiRequest("/api/auth/me");
}


// Resume upload
export async function uploadResume(file) {
    const formData = new FormData();
    formData.append("file", file);

    return apiRequest("/api/resume/upload", {
        method: "POST",
        body: formData
    });
}


// Start interview
export async function startInterview({
    interviewMode,
    role = null,
    jobDescription = null,
    difficulty,
    resumeId = null
}) {
    return apiRequest("/api/interview/start", {
        method: "POST",
        body: JSON.stringify({
            interview_mode: interviewMode,
            role,
            job_description: jobDescription,
            difficulty,
            resume_id: resumeId
        })
    });
}


// Submit text answer
export async function submitAnswer(sessionId, message) {
    return apiRequest("/api/interview/respond", {
        method: "POST",
        body: JSON.stringify({
            session_id: sessionId,
            message
        })
    });
}


// Get interview report
export async function getInterviewReport(sessionId) {
    return apiRequest(
        `/api/interview/report/${encodeURIComponent(sessionId)}`
    );
}


// Transcribe audio through HTTP, if this endpoint is still used
export async function transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    return apiRequest("/api/voice/transcribe", {
        method: "POST",
        body: formData
    });
}


// Dashboard summary
export async function getDashboardSummary() {
    return apiRequest("/api/dashboard/summary");
}


// Interview history
export async function getInterviewHistory() {
    return apiRequest("/api/dashboard/interviews");
}


// Interview details
export async function getInterviewDetails(interviewId) {
    return apiRequest(
        `/api/dashboard/interview/${encodeURIComponent(interviewId)}`
    );
}


// Authenticated WebSocket voice recording
export function sendVoiceRecording(sessionId, audioBlob) {
    return new Promise((resolve, reject) => {
        const token = getToken();

        if (!token) {
            reject(new Error("Please log in before starting an interview."));
            return;
        }

        const WS_URL = API_URL.replace(/^http/, "ws");

        const socket = new WebSocket(
            `${WS_URL}/api/voice/ws/${encodeURIComponent(sessionId)}`
        );

        let settled = false;
        let authenticated = false;

        function finish(callback, value) {
            if (settled) return;

            settled = true;
            socket.close();
            callback(value);
        }

        socket.onopen = () => {
            // First message authenticates the WebSocket
            socket.send(JSON.stringify({
                type: "authenticate",
                token
            }));
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === "error") {
                    finish(
                        reject,
                        new Error(data.message || "Voice processing failed.")
                    );
                    return;
                }

                if (data.type === "authenticated") {
                    if (authenticated) return;

                    authenticated = true;

                    // Send audio only after authentication succeeds
                    socket.send(audioBlob);
                    return;
                }

                if (data.type === "interview_response") {
                    if (!authenticated) {
                        finish(
                            reject,
                            new Error("WebSocket authentication was not completed.")
                        );
                        return;
                    }

                    finish(resolve, data);
                    return;
                }

                finish(
                    reject,
                    new Error("Unexpected response from voice server.")
                );

            } catch (error) {
                finish(reject, error);
            }
        };

        socket.onerror = () => {
            finish(
                reject,
                new Error("Could not connect to the voice WebSocket.")
            );
        };

        socket.onclose = () => {
            if (!settled) {
                finish(
                    reject,
                    new Error("Voice connection closed unexpectedly.")
                );
            }
        };
    });
}
