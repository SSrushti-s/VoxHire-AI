
import { useRef, useState } from "react";
import { Mic, Square } from "lucide-react";

function VoiceRecorder({ onRecordingComplete, disabled }) {
    const [recording, setRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            const recorder = new MediaRecorder(stream);

            mediaRecorderRef.current = recorder;
            chunksRef.current = [];

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            recorder.onstop = () => {
                const audioBlob = new Blob(chunksRef.current, {
                    type: recorder.mimeType || "audio/webm"
                });

                stream.getTracks().forEach(track => track.stop());

                onRecordingComplete(audioBlob);
            };

            recorder.start();
            setRecording(true);

        } catch (error) {
            console.error("Microphone error:", error);
            alert("Please allow microphone access.");
        }
    }

    function stopRecording() {
        if (mediaRecorderRef.current?.state === "recording") {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    }

    return (
        <button
            className={`mic-button ${recording ? "recording" : ""}`}
            onClick={recording ? stopRecording : startRecording}
            disabled={disabled}
        >
            {recording ? <Square size={22} /> : <Mic size={22} />}

            {recording ? "Stop recording" : "Start speaking"}
        </button>
    );
}

export default VoiceRecorder;
