
import { useState } from "react";

import {
    startInterview as startInterviewAPI,
    submitAnswer,
    transcribeAudio
} from "./services/api";

import VoiceRecorder from "./components/VoiceRecorder";
import ChatWindow from "./components/ChatWindow";

import {
    Bot,
    Volume2,
    BriefcaseBusiness,
    RotateCcw,
    Trophy
} from "lucide-react";

import "./App.css";


function App() {

    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const [interviewStarted, setInterviewStarted] = useState(false);
    const [interviewCompleted, setInterviewCompleted] = useState(false);

    const [role, setRole] = useState("React Developer");
    const [difficulty, setDifficulty] = useState("intermediate");

    const [sessionId, setSessionId] = useState(null);
    const [report, setReport] = useState(null);

    const [status, setStatus] = useState("Ready to interview");
    const [currentPhase, setCurrentPhase] = useState("Introduction");


    // Add a message to the chat
    function addMessage(role, content) {

        const message = {
            id: crypto.randomUUID(),
            role,
            content
        };

        setMessages(previous => [...previous, message]);
    }


    // Use browser speech as the current TTS provider
    function speak(text) {

        return new Promise((resolve, reject) => {

            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);

            utterance.lang = "en-US";
            utterance.rate = 1;
            utterance.pitch = 1;
            utterance.volume = 1;

            utterance.onend = () => resolve();

            utterance.onerror = (event) => {
                reject(
                    new Error(`Speech failed: ${event.error}`)
                );
            };

            window.speechSynthesis.speak(utterance);
        });
    }


    // Start a new interview
    async function startInterview() {

        try {

            setLoading(true);
            setStatus("Creating interview session...");

            const result = await startInterviewAPI(
                role,
                difficulty
            );

            setSessionId(result.session_id);
            setCurrentPhase(result.phase);

            setMessages([]);

            addMessage("assistant", result.question);

            setInterviewStarted(true);
            setInterviewCompleted(false);

            setStatus("Interview in progress");

            await speak(result.question);

        } catch (error) {

            console.error(error);
            setStatus(error.message);

        } finally {

            setLoading(false);

        }
    }


    // Process the candidate's voice answer
    async function handleRecording(audioBlob) {

        try {

            setLoading(true);

            setStatus("Transcribing your answer...");

            // Step 1: Convert audio into text
            const transcription = await transcribeAudio(audioBlob);

            const userMessage = transcription.transcript;

            if (!userMessage || !userMessage.trim()) {

                setStatus("No speech detected. Try again.");
                return;
            }

            addMessage("user", userMessage);


            // Step 2: Send answer to the interview engine
            setStatus("Evaluating your answer...");

            const result = await submitAnswer(
                sessionId,
                userMessage
            );


            // Step 3: Display evaluation feedback
            if (result.evaluation) {

                const evaluation = result.evaluation;

                addMessage(
                    "assistant",
                    `Score: ${evaluation.score}/10. ${evaluation.feedback}`
                );

            }


            // Step 4: Display the next question
            const nextQuestion = result.response;

            addMessage("assistant", nextQuestion);

            setCurrentPhase(result.current_phase);


            // Step 5: Handle interview completion
            if (result.interview_completed) {

                setInterviewCompleted(true);
                setReport(result.report);

                setStatus("Interview completed!");

            } else {

                setStatus("Interview in progress");

            }


            // Step 6: Speak the response
            await speak(nextQuestion);

            if (result.interview_completed) {
                setStatus("Interview completed!");
            } else {
                setStatus("Interview in progress");
            }


        } catch (error) {

            console.error(error);
            setStatus(error.message);

        } finally {

            setLoading(false);

        }
    }


    // Reset interview
    function resetInterview() {

        window.speechSynthesis.cancel();

        setMessages([]);
        setInterviewStarted(false);
        setInterviewCompleted(false);

        setSessionId(null);
        setReport(null);

        setCurrentPhase("Introduction");
        setStatus("Ready to interview");
    }


    return (

        <div className="app">

            <header className="header">

                <div className="brand">
                    <Bot size={30} />
                    <h1>VoxHire AI</h1>
                </div>

                <span className="status">
                    {status}
                </span>

            </header>


            <main className="main-container">

                <section className="welcome-section">

                    <h2>Your AI Interview Partner</h2>

                    <p>
                        Practice interviews through natural voice
                        conversations and improve your technical skills.
                    </p>

                </section>


                <section className="interview-card">

                    {!interviewStarted ? (

                        <div className="setup">

                            <BriefcaseBusiness size={35} />

                            <h2>Configure your interview</h2>


                            <label>Select your job role</label>

                            <select
                                value={role}
                                onChange={(event) =>
                                    setRole(event.target.value)
                                }
                            >

                                <option>React Developer</option>
                                <option>Full Stack Developer</option>
                                <option>Python Developer</option>
                                <option>AI Engineer</option>

                            </select>


                            <label>Select difficulty</label>

                            <select
                                value={difficulty}
                                onChange={(event) =>
                                    setDifficulty(event.target.value)
                                }
                            >

                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>

                            </select>


                            <button
                                className="primary-button"
                                onClick={startInterview}
                                disabled={loading}
                            >

                                {loading
                                    ? "Starting..."
                                    : "Start Interview"
                                }

                            </button>

                        </div>

                    ) : (

                        <>

                            <div className="chat-header">

                                <div>
                                    <h2>Interview Session</h2>

                                    <p>
                                        {role} · {currentPhase}
                                    </p>
                                </div>


                                <button
                                    className="reset-button"
                                    onClick={resetInterview}
                                    disabled={loading}
                                >

                                    <RotateCcw size={17} />
                                    Reset

                                </button>

                            </div>


                            <ChatWindow
                                messages={messages}
                                loading={loading}
                            />


                            {!interviewCompleted && (

                                <div className="voice-controls">

                                    <VoiceRecorder
                                        onRecordingComplete={handleRecording}
                                        disabled={loading}
                                    />

                                    <p>
                                        <Volume2 size={16} />
                                        Speak your answer using your microphone
                                    </p>

                                </div>

                            )}


                            {interviewCompleted && report && (

                                <div className="report-card">

                                    <Trophy size={35} />

                                    <h2>Interview Completed!</h2>

                                    <h3>Performance Report</h3>

                                    <p>
                                        Role: <strong>{report.role}</strong>
                                    </p>

                                    <div className="score-display">

                                        {report.overall_score}/10

                                        <span>Average score</span>

                                    </div>

                                    <p>
                                        Total answers evaluated:
                                        <strong> {report.total_answers}</strong>
                                    </p>


                                    <h3>Strengths</h3>

                                    <ul>

                                        {report.strengths.map(
                                            (item, index) => (
                                                <li key={index}>{item}</li>
                                            )
                                        )}

                                    </ul>


                                    <h3>Areas to improve</h3>

                                    <ul>

                                        {report.improvements.map(
                                            (item, index) => (
                                                <li key={index}>{item}</li>
                                            )
                                        )}

                                    </ul>


                                    <button
                                        className="primary-button"
                                        onClick={resetInterview}
                                    >

                                        Start New Interview

                                    </button>

                                </div>

                            )}

                        </>

                    )}

                </section>

            </main>

        </div>

    );

}

export default App;
