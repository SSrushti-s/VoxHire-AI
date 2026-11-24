import { useState, useEffect } from "react";
import Login from "./components/Login";
import Signup from "./components/Signup";

import {
    getToken,
    getCurrentUser,
    logout
} from "./services/api";
import {
    startInterview as startInterviewAPI,
    uploadResume,
    sendVoiceRecording
} from "./services/api";
import CareerDashboard from "./components/CareerDashboard";
import VoiceRecorder from "./components/VoiceRecorder";
import ChatWindow from "./components/ChatWindow";

import {
    Bot,
    Volume2,
    BriefcaseBusiness,
    RotateCcw,
    Trophy,
    FileText,
    Upload,
    X
} from "lucide-react";

import "./App.css";


function App() {

    const [user, setUser] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);
    const [authPage, setAuthPage] = useState("login");

    useEffect(() => {
        async function checkAuthentication() {
            const token = getToken();

            if (!token) {
                setAuthLoading(false);
                return;
            }

            try {
                const result = await getCurrentUser();
                setUser(result.user);
            } catch (error) {
                console.error("AUTHENTICATION ERROR:", error);
                logout();
                setUser(null);
            } finally {
                setAuthLoading(false);
            }
        }

        checkAuthentication();
    }, []);

    function handleAuthSuccess(userData) {
        setUser(userData);
    }

    function handleLogout() {
        logout();
        window.location.reload();
    }
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    // Persistent demo candidate identity

    const [dashboardRefresh, setDashboardRefresh] = useState(0);
    const [interviewStarted, setInterviewStarted] = useState(false);
    const [interviewCompleted, setInterviewCompleted] = useState(false);

    const [interviewMode, setInterviewMode] = useState("role");
    const [role, setRole] = useState("React Developer");
    const [jobDescription, setJobDescription] = useState("");
    const [difficulty, setDifficulty] = useState("intermediate");

    const [sessionId, setSessionId] = useState(null);
    const [report, setReport] = useState(null);

    const [status, setStatus] = useState("Ready to interview");
    const [currentPhase, setCurrentPhase] = useState("Introduction");

    // Stage 3.6 - Resume states
    const [resumeId, setResumeId] = useState(null);
    const [resumeFile, setResumeFile] = useState(null);
    const [candidateProfile, setCandidateProfile] = useState(null);
    const [resumeUploading, setResumeUploading] = useState(false);


    // Add a message to the chat
    function addMessage(role, content) {

        const message = {
            id: crypto.randomUUID(),
            role,
            content
        };

        setMessages(previous => [...previous, message]);
    }


    // Stage 3.6 - Upload and analyze resume
    async function handleResumeUpload(event) {

        const file = event.target.files?.[0];

        if (!file) return;

        // Validate file type
        if (file.type !== "application/pdf") {
            setStatus("Please upload a PDF resume.");
            event.target.value = "";
            return;
        }

        // Validate file size: maximum 10 MB
        if (file.size > 10 * 1024 * 1024) {
            setStatus("Resume must be smaller than 10 MB.");
            event.target.value = "";
            return;
        }

        try {

            setResumeUploading(true);
            setStatus("Uploading and analyzing resume...");

            // Send PDF to FastAPI
            const result = await uploadResume(file);

            // Save generated resume ID
            setResumeId(result.resume_id);

            // Save extracted candidate information
            setCandidateProfile(result.candidate_profile);

            setResumeFile(file);

            setStatus("Resume uploaded and analyzed successfully!");

        } catch (error) {

            console.error("RESUME UPLOAD ERROR:", error);

            setResumeId(null);
            setCandidateProfile(null);
            setResumeFile(null);

            setStatus(error.message);

        } finally {

            setResumeUploading(false);

            // Allow selecting the same file again
            event.target.value = "";
        }
    }


    // Remove uploaded resume
    function removeResume() {

        setResumeId(null);
        setResumeFile(null);
        setCandidateProfile(null);

        setStatus("Resume removed. You can continue without a resume.");
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

        if (
            interviewMode === "job_description" &&
            !jobDescription.trim()
        ) {
            setStatus("Please enter a job description.");
            return;
        }

        try {
            setLoading(true);
            setStatus("Creating interview session...");

            const result = await startInterviewAPI({
                interviewMode,
                role: interviewMode === "role" ? role : null,
                jobDescription:
                    interviewMode === "job_description"
                        ? jobDescription.trim()
                        : null,
                difficulty,
                resumeId
            });

            setSessionId(result.session_id);
            setCurrentPhase(result.phase);

            setMessages([]);
            addMessage("assistant", result.question);

            setInterviewStarted(true);
            setInterviewCompleted(false);

            setStatus(
                resumeId
                    ? "Starting your personalized interview..."
                    : "Interview in progress"
            );

            await speak(result.question);

            setStatus("Interview in progress");

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
            setStatus("Sending audio to VoxHire AI...");

            // Step 1: Send the complete recording through WebSocket
            const voiceResult = await sendVoiceRecording(
                sessionId,
                audioBlob
            );

            // Step 2: Get the recognized speech
            const userMessage = voiceResult.transcript;

            if (!userMessage || !userMessage.trim()) {

                setStatus("No speech detected. Try again.");
                return;
            }

            addMessage("user", userMessage);

            // Step 3: Get LangGraph's interview response
            const result = voiceResult.result;

            // Step 4: Display evaluation feedback
            if (result.evaluation) {

                const evaluation = result.evaluation;

                addMessage(
                    "assistant",
                    `Score: ${evaluation.score}/10. ${evaluation.feedback}`
                );
            }

            // Step 5: Display the next question or final response
            const nextQuestion = result.response;

            if (nextQuestion) {
                addMessage("assistant", nextQuestion);
            }

            setCurrentPhase(result.current_phase);

            // Step 6: Handle interview completion
            if (result.interview_completed) {

                setInterviewCompleted(true);
                setReport(result.report);

                // Refresh dashboard after backend persistence attempt
                setDashboardRefresh(previous => previous + 1);

                if (result.persistence_saved) {
                    setStatus("Interview completed and saved!");
                } else {
                    setStatus(
                        "Interview completed, but MongoDB saving needs attention."
                    );
                }

            } else {

                setStatus("Interview in progress");

            }

            // Step 7: Speak the AI response
            if (nextQuestion) {
                await speak(nextQuestion);
            }

            if (result.interview_completed) {
                setStatus("Interview completed!");
            } else {
                setStatus("Interview in progress");
            }

        } catch (error) {

            console.error("VOICE INTERVIEW ERROR:", error);
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

        // Keep the uploaded resume available for another interview
    }

    if (authLoading) {
        return <div className="auth-container">Checking your session...</div>;
    }

    if (!user) {
        return authPage === "login" ? (
            <Login
                onSuccess={handleAuthSuccess}
                onSwitch={() => setAuthPage("signup")}
            />
        ) : (
            <Signup
                onSuccess={handleAuthSuccess}
                onSwitch={() => setAuthPage("login")}
            />
        );
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

                <div className="user-header">
                    <span>Welcome, {user.name}</span>

                    <button
                        type="button"
                        onClick={handleLogout}
                        className="logout-button"
                    >
                        Logout
                    </button>
                </div>
            </header>


            <main className="main-container">

                <section className="welcome-section">

                    <h2>Your AI Interview Partner</h2>

                    <p>
                        Practice interviews through natural voice
                        conversations and improve your technical skills.
                    </p>

                </section>

                <CareerDashboard
                    refreshKey={dashboardRefresh}
                />

                <section className="interview-card">

                    {!interviewStarted ? (

                        <div className="setup">

                            <BriefcaseBusiness size={35} />

                            <h2>Configure your interview</h2>


                            <label>Choose interview type</label>

                            <select
                                value={interviewMode}
                                onChange={(event) =>
                                    setInterviewMode(event.target.value)
                                }
                            >
                                <option value="role">Job Role</option>
                                <option value="job_description">Job Description</option>
                            </select>


                            {interviewMode === "role" ? (

                                <>
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
                                </>

                            ) : (

                                <>
                                    <label>Paste your Job Description</label>

                                    <textarea
                                        className="jd-input"
                                        value={jobDescription}
                                        onChange={(event) =>
                                            setJobDescription(event.target.value)
                                        }
                                        placeholder="Paste the complete job description here..."
                                        rows={8}
                                        maxLength={15000}
                                    />

                                    <small>
                                        Include the responsibilities, required skills
                                        and qualifications for the position.
                                    </small>
                                </>

                            )}


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


                            {/* Stage 3.6 - Resume upload */}

                            <div className="resume-section">

                                <h3>
                                    <FileText size={20} />
                                    Resume Intelligence
                                </h3>

                                <p>
                                    Upload your resume to receive
                                    personalized interview questions.
                                </p>


                                {!resumeFile ? (

                                    <label className="resume-upload">

                                        <Upload size={22} />

                                        <span>
                                            {resumeUploading
                                                ? "Analyzing resume..."
                                                : "Upload your resume (PDF)"
                                            }
                                        </span>

                                        <input
                                            type="file"
                                            accept=".pdf,application/pdf"
                                            onChange={handleResumeUpload}
                                            disabled={resumeUploading || loading}
                                        />

                                    </label>

                                ) : (

                                    <div className="uploaded-resume">

                                        <FileText size={22} />

                                        <div className="resume-file-info">

                                            <strong>{resumeFile.name}</strong>

                                            <span>
                                                Resume analyzed successfully
                                            </span>

                                        </div>

                                        <button
                                            type="button"
                                            onClick={removeResume}
                                            disabled={resumeUploading || loading}
                                            title="Remove resume"
                                        >
                                            <X size={18} />
                                        </button>

                                    </div>

                                )}


                                {candidateProfile && (

                                    <div className="profile-preview">

                                        <h4>Extracted Candidate Profile</h4>

                                        {candidateProfile.candidate_name && (
                                            <p>
                                                <strong>Name:</strong>{" "}
                                                {candidateProfile.candidate_name}
                                            </p>
                                        )}

                                        {candidateProfile.summary && (
                                            <p>
                                                <strong>Summary:</strong>{" "}
                                                {candidateProfile.summary}
                                            </p>
                                        )}


                                        {candidateProfile.skills && (

                                            <div className="profile-skills">

                                                <strong>Detected Skills</strong>

                                                <div className="skill-tags">

                                                    {Object.entries(
                                                        candidateProfile.skills
                                                    ).map(([category, skills]) => (

                                                        Array.isArray(skills) && skills.map(
                                                            (skill, index) => (

                                                                <span
                                                                    key={`${category}-${index}`}
                                                                    className="skill-tag"
                                                                    title={category.replaceAll("_", " ")}
                                                                >
                                                                    {skill}
                                                                </span>

                                                            )
                                                        )

                                                    ))}

                                                </div>

                                            </div>

                                        )}

                                    </div>

                                )}

                            </div>


                            <button
                                className="primary-button"
                                onClick={startInterview}
                                disabled={loading || resumeUploading}
                            >

                                {loading
                                    ? "Starting..."
                                    : resumeUploading
                                        ? "Analyzing Resume..."
                                        : resumeId
                                            ? "Start Personalized Interview"
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
                                        {interviewMode === "role"
                                            ? role
                                            : "Job Description Interview"}
                                        {" · "}{currentPhase}

                                        {resumeId && " · Resume-based"}
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