
import React, { useRef, useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_BASE_URL;

const WS_URL = API_URL
    ? API_URL.replace(/^http/, "ws")
    : "ws://localhost:8000";

function RealtimeVoice({ sessionId, onResponse }) {
    const [recording, setRecording] = useState(false);
    const [connected, setConnected] = useState(false);
    const [status, setStatus] = useState("Connect to begin");

    const socketRef = useRef(null);
    const recorderRef = useRef(null);
    const streamRef = useRef(null);

    useEffect(() => {
        if (!sessionId) return;

        const socket = new WebSocket(
            `${WS_URL}/api/voice/ws/${sessionId}`
        );

        socketRef.current = socket;

        socket.onopen = () => {
            setConnected(true);
            setStatus("Connected. Ready to speak.");
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "error") {
                setStatus(data.message);
                return;
            }

            if (data.type === "interview_response") {
                setStatus("Response received.");

                onResponse?.(data);

                const responseText =
                    data.result?.next_question ||
                    data.result?.message ||
                    data.result?.feedback ||
                    "";

                if (responseText) {
                    window.speechSynthesis.cancel();

                    const utterance =
                        new SpeechSynthesisUtterance(responseText);

                    utterance.lang = "en-US";

                    window.speechSynthesis.speak(utterance);
                }
            }
        };

        socket.onerror = () => {
            setStatus("Connection error.");
        };

        socket.onclose = () => {
            setConnected(false);
            setStatus("Disconnected.");
        };

        return () => {
            socket.close();
            window.speechSynthesis.cancel();

            streamRef.current?.getTracks().forEach(
                track => track.stop()
            );
        };
    }, [sessionId]);

    async function startRecording() {
        try {
            if (!socketRef.current ||
                socketRef.current.readyState !== WebSocket.OPEN) {
                setStatus("WebSocket is not connected.");
                return;
            }

            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true
                });

            streamRef.current = stream;

            const recorder = new MediaRecorder(stream);

            recorderRef.current = recorder;

            const chunks = [];

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };

            recorder.onstop = async () => {
                const audioBlob = new Blob(chunks, {
                    type: recorder.mimeType
                });

                if (audioBlob.size > 0 &&
                    socketRef.current?.readyState === WebSocket.OPEN) {
                    setStatus("Processing your answer...");

                    const audioBuffer =
                        await audioBlob.arrayBuffer();

                    socketRef.current.send(audioBuffer);
                }

                stream.getTracks().forEach(
                    track => track.stop()
                );
            };

            recorder.start();

            setRecording(true);
            setStatus("Listening...");
        } catch (error) {
            console.error(error);
            setStatus("Microphone permission denied or unavailable.");
        }
    }

    function stopRecording() {
        if (recorderRef.current?.state === "recording") {
            recorderRef.current.stop();
            setRecording(false);
            setStatus("Uploading audio...");
        }
    }

    return (
        <div className="realtime-voice">
            <h3>🎙️ Live Voice Interview</h3>

            <p>
                {connected ? "🟢 Connected" : "🔴 Disconnected"}
            </p>

            <p>{status}</p>

            {!recording ? (
                <button
                    onClick={startRecording}
                    disabled={!connected}
                >
                    🎤 Start Speaking
                </button>
            ) : (
                <button onClick={stopRecording}>
                    ⏹ Stop and Submit
                </button>
            )}
        </div>
    );
}

export default RealtimeVoice;
