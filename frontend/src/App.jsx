import { useState, useEffect, useRef } from "react";
import Login from "./components/Login";
import Signup from "./components/Signup";

import {
    getToken,
    getCurrentUser,
    logout,
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
    X,
    ArrowUpRight,
    CheckCircle2,
    Sparkles,
    Mic,
    BarChart3,
    MessageSquare,
    ChevronDown
} from "lucide-react";

import interviewIllustration from "./assets/interview-illustration.png";
import "./App.css";

function App() {
    const [user, setUser] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);
    const [authPage, setAuthPage] = useState("login");
    const [activeNav, setActiveNav] = useState("home");

    const setupSectionRef = useRef(null);
    const dashboardSectionRef = useRef(null);
    const featuresSectionRef = useRef(null);

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

    function scrollToSection(ref, navName) {
        setActiveNav(navName);
        ref.current?.scrollIntoView({ behavior: "smooth" });
    }

    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

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

    // Resume states
    const [resumeId, setResumeId] = useState(null);
    const [resumeFile, setResumeFile] = useState(null);
    const [candidateProfile, setCandidateProfile] = useState(null);
    const [resumeUploading, setResumeUploading] = useState(false);

    function addMessage(role, content) {
        const message = {
            id: crypto.randomUUID(),
            role,
            content
        };
        setMessages((previous) => [...previous, message]);
    }

    async function handleResumeUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;

        if (file.type !== "application/pdf") {
            setStatus("Please upload a PDF resume.");
            event.target.value = "";
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            setStatus("Resume must be smaller than 10 MB.");
            event.target.value = "";
            return;
        }

        try {
            setResumeUploading(true);
            setStatus("Uploading and analyzing resume...");

            const result = await uploadResume(file);
            setResumeId(result.resume_id);
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
            event.target.value = "";
        }
    }

    function removeResume() {
        setResumeId(null);
        setResumeFile(null);
        setCandidateProfile(null);
        setStatus("Resume removed. You can continue without a resume.");
    }

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
                reject(new Error(`Speech failed: ${event.error}`));
            };

            window.speechSynthesis.speak(utterance);
        });
    }

    async function startInterview() {
        if (interviewMode === "job_description" && !jobDescription.trim()) {
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

    async function handleRecording(audioBlob) {
        try {
            setLoading(true);
            setStatus("Sending audio to VoxHire AI...");

            const voiceResult = await sendVoiceRecording(sessionId, audioBlob);
            const userMessage = voiceResult.transcript;

            if (!userMessage || !userMessage.trim()) {
                setStatus("No speech detected. Try again.");
                return;
            }

            addMessage("user", userMessage);

            const result = voiceResult.result;

            if (result.evaluation) {
                const evaluation = result.evaluation;
                addMessage(
                    "assistant",
                    `Score: ${evaluation.score}/10. ${evaluation.feedback}`
                );
            }

            const nextQuestion = result.response;
            if (nextQuestion) {
                addMessage("assistant", nextQuestion);
            }

            setCurrentPhase(result.current_phase);

            if (result.interview_completed) {
                setInterviewCompleted(true);
                setReport(result.report);
                setDashboardRefresh((previous) => previous + 1);

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

    if (authLoading) {
        return <div className="auth-container">Checking your session...</div>;
    }

    if (!user) {
        return (
            <div
                className={`auth-page ${authPage === "signup" ? "signup-active" : ""}`}
            >
                <section className="auth-visual">
                    <div className="auth-brand">
                        <span className="auth-brand-icon">✳</span>
                        <span>VoxHire AI</span>
                    </div>

                    <div className="auth-visual-content">
                        <div className="auth-eyebrow">
                            <span className="auth-eyebrow-dot"></span>
                            {authPage === "login"
                                ? "AI-POWERED INTERVIEW PREPARATION"
                                : "YOUR INTERVIEW JOURNEY BEGINS"}
                        </div>

                        <h1>
                            {authPage === "login" ? (
                                <>
                                    Your next big
                                    <br />
                                    opportunity
                                    <br />
                                    starts <span>here.</span>
                                </>
                            ) : (
                                <>
                                    Meet your
                                    <br />
                                    future with
                                    <br />
                                    <span>confidence.</span>
                                </>
                            )}
                        </h1>

                        <p>
                            {authPage === "login"
                                ? "Practice smarter, speak confidently, and prepare for your dream job with your personal AI interviewer."
                                : "Create your account and start preparing for interviews with personalized AI-powered practice sessions."}
                        </p>

                        {/* Illustration */}
                    <div className="auth-illustration">
                        <img
                            src={interviewIllustration}
                            alt="Candidate attending an online AI interview"
                            className="auth-illustration-img"
                        />

                        <div className="illustration-caption">
                            <span>YOUR AI INTERVIEWER</span>
                            <strong>
                                {authPage === "login"
                                    ? "Let's get you hired!"
                                    : "Your future starts today!"
                                }
                            </strong>
                        </div>
                    </div>
                    </div>

                    <div className="auth-visual-footer">
                        © 2026 VoxHire AI. All rights reserved.
                    </div>
                </section>

                <Login
                    onSuccess={handleAuthSuccess}
                    onSwitch={() => setAuthPage("signup")}
                />

                <Signup
                    onSuccess={handleAuthSuccess}
                    onSwitch={() => setAuthPage("login")}
                />
            </div>
        );
    }

    const sampleQuestions = [
        { step: 1, text: "Tell us about yourself?", active: true },
        { step: 2, text: "Why do you think you are good at this role?", active: true },
        { step: 3, text: "What is the biggest deal or project you closed?", active: false },
        { step: 4, text: "Why did you leave your previous company?", active: false },
        { step: 5, text: "What are your expectations in this role?", active: false },
        { step: 6, text: "Do you have any questions for our team?", active: false }
    ];

    return (
        <div className="vh-home">
            {/* TOP PILL NAVIGATION */}
            <header className="vh-navbar">
                <div className="vh-nav-brand">
                    <span className="vh-logo-badge">
                        <Bot size={20} />
                    </span>
                    <span className="vh-logo-text">VoxHire AI</span>
                </div>

                <nav className="vh-nav-pill" aria-label="Primary navigation">
                    <button
                        type="button"
                        className={`vh-pill-link ${activeNav === "home" ? "active" : ""}`}
                        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
                    >
                        Home
                    </button>
                    <button
                        type="button"
                        className={`vh-pill-link ${activeNav === "dashboard" ? "active" : ""}`}
                        onClick={() => scrollToSection(dashboardSectionRef, "dashboard")}
                    >
                        Analytics
                    </button>
                    <button
                        type="button"
                        className={`vh-pill-link ${activeNav === "features" ? "active" : ""}`}
                        onClick={() => scrollToSection(featuresSectionRef, "features")}
                    >
                        Features <ChevronDown size={14} />
                    </button>
                    <button
                        type="button"
                        className={`vh-pill-link ${activeNav === "practice" ? "active" : ""}`}
                        onClick={() => scrollToSection(setupSectionRef, "practice")}
                    >
                        Practice Lab
                    </button>
                </nav>

                <div className="vh-nav-actions">
                    <span className="vh-status-pill" title="System status">
                        <span className="vh-status-dot"></span>
                        {status}
                    </span>

                    <button
                        type="button"
                        className="vh-btn-primary"
                        onClick={() => scrollToSection(setupSectionRef, "practice")}
                    >
                        Start Interview
                    </button>

                    <button
                        type="button"
                        onClick={handleLogout}
                        className="vh-btn-ghost"
                    >
                        Logout ({user.name})
                    </button>
                </div>
            </header>

            <main className="vh-container">
                {/* HERO SECTION (MATCHING REFERENCE LAYOUT) */}
                {!interviewStarted && (
                    <section className="vh-hero">
                        <div className="vh-hero-top">
                            <h1 className="vh-hero-title">
                                All-In-One AI
                                <br />
                                Interview Platform
                            </h1>

                            <div className="vh-hero-right">
                                <p className="vh-hero-desc">
                                    Welcome back, <strong>{user.name}</strong>. VoxHire AI
                                    combines natural voice intelligence with real-time answer
                                    evaluation to sharpen your technical and behavioral
                                    interview skills.
                                </p>

                                <div className="vh-hero-cta-group">
                                    <button
                                        type="button"
                                        className="vh-btn-primary"
                                        onClick={() =>
                                            scrollToSection(setupSectionRef, "practice")
                                        }
                                    >
                                        Start Session
                                    </button>
                                    <button
                                        type="button"
                                        className="vh-btn-outline"
                                        onClick={() =>
                                            scrollToSection(dashboardSectionRef, "dashboard")
                                        }
                                    >
                                        View Progress <ArrowUpRight size={15} />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* BENTO PREVIEW GRID */}
                        <div className="vh-bento-grid">
                            {/* Column 1: Question List Card */}
                            <div className="vh-card vh-question-card">
                                <div className="vh-card-header">
                                    <h3>Question List</h3>
                                    <span className="vh-icon-circle">
                                        <MessageSquare size={14} />
                                    </span>
                                </div>

                                <ul className="vh-question-timeline">
                                    {sampleQuestions.map((item) => (
                                        <li
                                            key={item.step}
                                            className={item.active ? "active" : ""}
                                        >
                                            <span className="vh-step-dot">{item.step}</span>
                                            <p>{item.text}</p>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Column 2: Feedback & Candidate Card */}
                            <div className="vh-bento-middle">
                                <div className="vh-card vh-feedback-card">
                                    <div className="vh-card-header">
                                        <div>
                                            <h4>Real-Time Evaluation</h4>
                                            <span className="vh-muted">
                                                AI scoring across key criteria
                                            </span>
                                        </div>
                                    </div>

                                    <div className="vh-evaluator-list">
                                        <div className="vh-evaluator-item">
                                            <div className="vh-avatar emerald">TC</div>
                                            <div>
                                                <strong>Technical Clarity</strong>
                                                <span>Architecture &amp; depth · ★★★★★</span>
                                            </div>
                                        </div>
                                        <div className="vh-evaluator-item">
                                            <div className="vh-avatar slate">CS</div>
                                            <div>
                                                <strong>Communication</strong>
                                                <span>Pacing &amp; structure · ★★★★☆</span>
                                            </div>
                                        </div>
                                        <div className="vh-evaluator-item">
                                            <div className="vh-avatar teal">RM</div>
                                            <div>
                                                <strong>Resume Alignment</strong>
                                                <span>Project ownership · ★★★★★</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="vh-card vh-candidate-banner">
                                    <div className="vh-candidate-badge">
                                        <Mic size={16} />
                                        <div>
                                            <strong>{user.name}</strong>
                                            <span>{role} Track</span>
                                        </div>
                                    </div>
                                    <div className="vh-live-tag">● Voice Ready</div>
                                </div>
                            </div>

                            {/* Column 3: Main Interview Stage Preview */}
                            <div className="vh-card vh-stage-card">
                                <div className="vh-stage-header">
                                    <div className="vh-stage-pills">
                                        <span className="vh-chip">AI Voice</span>
                                        <span className="vh-chip">Live Scoring</span>
                                        <span className="vh-chip">Resume Sync</span>
                                    </div>
                                    <span className="vh-rating">★★★★★ 4.9</span>
                                </div>

                                <div className="vh-stage-screen">
                                    <div className="vh-stage-ai-orb">
                                        <Bot size={38} />
                                    </div>
                                    <p className="vh-stage-prompt">
                                        &ldquo;Walk me through how you optimize state and
                                        rendering performance in a production{" "}
                                        <strong>{role}</strong> application.&rdquo;
                                    </p>
                                </div>

                                <div className="vh-stage-metrics">
                                    <div className="vh-metric-box">
                                        <span className="vh-muted">Readiness Score</span>
                                        <strong>88%</strong>
                                    </div>
                                    <div className="vh-ring-group">
                                        <div className="vh-ring-item">
                                            <div className="vh-ring">78%</div>
                                            <span>Clarity</span>
                                        </div>
                                        <div className="vh-ring-item">
                                            <div className="vh-ring">85%</div>
                                            <span>Depth</span>
                                        </div>
                                        <div className="vh-ring-item">
                                            <div className="vh-ring">92%</div>
                                            <span>Confidence</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* KEY FEATURES SECTION (MATCHING REFERENCE SECTION 2) */}
                {!interviewStarted && (
                    <section className="vh-features-section" ref={featuresSectionRef}>
                        <div className="vh-features-head">
                            <h2>
                                Key Features for
                                <br />
                                Smarter Practice
                            </h2>
                            <p>
                                Our AI interviewer adapts to your target role, parses your
                                PDF resume, and delivers structured feedback after every
                                spoken response.
                            </p>
                        </div>

                        <div className="vh-features-grid">
                            <div className="vh-feature-card emerald-solid">
                                <Sparkles size={24} />
                                <h3>Personalized Resume Screening</h3>
                                <p>
                                    Upload your PDF resume to extract skills and generate
                                    tailored follow-up questions grounded in your actual
                                    experience.
                                </p>
                                <button
                                    type="button"
                                    className="vh-btn-white"
                                    onClick={() =>
                                        scrollToSection(setupSectionRef, "practice")
                                    }
                                >
                                    Upload Resume
                                </button>
                            </div>

                            <div className="vh-feature-card">
                                <BarChart3 size={24} className="vh-accent-icon" />
                                <h3>Behavioral &amp; Technical Analysis</h3>
                                <p>
                                    Evaluate clarity, problem-solving structure, and domain
                                    knowledge across Beginner, Intermediate, and Advanced
                                    levels.
                                </p>
                                <button
                                    type="button"
                                    className="vh-btn-primary"
                                    onClick={() =>
                                        scrollToSection(dashboardSectionRef, "dashboard")
                                    }
                                >
                                    See Analytics
                                </button>
                            </div>

                            <div className="vh-feature-card">
                                <CheckCircle2 size={24} className="vh-accent-icon" />
                                <h3>Real-Time Voice Feedback</h3>
                                <p>
                                    Speak naturally through your microphone and receive an
                                    instant 1–10 score with actionable coaching tips.
                                </p>
                                <button
                                    type="button"
                                    className="vh-btn-primary"
                                    onClick={() =>
                                        scrollToSection(setupSectionRef, "practice")
                                    }
                                >
                                    Try Voice Mode
                                </button>
                            </div>
                        </div>
                    </section>
                )}

                {/* CAREER ANALYTICS DASHBOARD */}
                <div ref={dashboardSectionRef} className="vh-dashboard-wrap">
                    <CareerDashboard refreshKey={dashboardRefresh} />
                </div>

                {/* INTERACTIVE INTERVIEW CONFIGURATION & LIVE SESSION */}
                <section className="interview-card vh-workspace-card" ref={setupSectionRef}>
                    {!interviewStarted ? (
                        <div className="setup">
                            <div className="vh-setup-header">
                                <span className="vh-icon-circle large">
                                    <BriefcaseBusiness size={24} />
                                </span>
                                <div>
                                    <h2>Configure Your Interview</h2>
                                    <p className="vh-muted">
                                        Choose a role or paste a job description to launch
                                        your AI voice session.
                                    </p>
                                </div>
                            </div>

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
                                        onChange={(event) => setRole(event.target.value)}
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
                                        Include the responsibilities, required skills and
                                        qualifications for the position.
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

                            {/* Resume upload */}
                            <div className="resume-section">
                                <h3>
                                    <FileText size={20} />
                                    Resume Intelligence
                                </h3>
                                <p>
                                    Upload your resume to receive personalized interview
                                    questions.
                                </p>

                                {!resumeFile ? (
                                    <label className="resume-upload">
                                        <Upload size={22} />
                                        <span>
                                            {resumeUploading
                                                ? "Analyzing resume..."
                                                : "Upload your resume (PDF)"}
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
                                            <span>Resume analyzed successfully</span>
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
                                                    ).map(([category, skills]) =>
                                                        Array.isArray(skills) &&
                                                        skills.map((skill, index) => (
                                                            <span
                                                                key={`${category}-${index}`}
                                                                className="skill-tag"
                                                                title={category.replaceAll(
                                                                    "_",
                                                                    " "
                                                                )}
                                                            >
                                                                {skill}
                                                            </span>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <button
                                className="primary-button vh-btn-primary full"
                                onClick={startInterview}
                                disabled={loading || resumeUploading}
                            >
                                {loading
                                    ? "Starting..."
                                    : resumeUploading
                                      ? "Analyzing Resume..."
                                      : resumeId
                                        ? "Start Personalized Interview"
                                        : "Start Interview"}
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
                                        {" · "}
                                        {currentPhase}
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

                            <ChatWindow messages={messages} loading={loading} />

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
                                        {report.strengths.map((item, index) => (
                                            <li key={index}>{item}</li>
                                        ))}
                                    </ul>

                                    <h3>Areas to improve</h3>
                                    <ul>
                                        {report.improvements.map((item, index) => (
                                            <li key={index}>{item}</li>
                                        ))}
                                    </ul>

                                    <button
                                        className="primary-button vh-btn-primary"
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