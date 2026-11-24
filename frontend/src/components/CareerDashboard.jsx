import { useEffect, useState } from "react";
import {
    BarChart3,
    Award,
    Target,
    History,
    Calendar,
    Briefcase,
    CheckCircle2
} from "lucide-react";

import {
    getDashboardSummary,
    getInterviewHistory
} from "../services/api";

export default function CareerDashboard({ refreshKey = 0 }) {
    const [summary, setSummary] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;

        async function loadDashboard() {
            try {
                setLoading(true);
                setError("");

                const [summaryData, historyData] = await Promise.all([
                    getDashboardSummary(),
                    getInterviewHistory()
                ]);

                if (!active) return;

                setSummary(summaryData);
                setHistory(Array.isArray(historyData) ? historyData : []);
            } catch (error) {
                if (active) {
                    setError(error.message);
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        loadDashboard();

        return () => {
            active = false;
        };
    }, [refreshKey]);

    if (loading) {
        return (
            <section className="dashboard-card vh-dashboard-card">
                <p className="vh-dashboard-loading">Loading career analytics...</p>
            </section>
        );
    }

    if (error) {
        return (
            <section className="dashboard-card vh-dashboard-card">
                <h2>Career Dashboard</h2>
                <p className="vh-dashboard-error">{error}</p>
            </section>
        );
    }

    const totalInterviews = summary?.total_interviews ?? 0;
    const overallScore = summary?.overall_score ?? 0;
    const skillCoverage = summary?.skill_coverage ?? 0;

    return (
        <section className="dashboard-card vh-dashboard-card">
            <div className="vh-dashboard-header">
                <div className="vh-dashboard-title-group">
                    <span className="vh-icon-circle large">
                        <BarChart3 size={22} />
                    </span>
                    <div>
                        <h2>Your Career Dashboard</h2>
                        <p className="vh-muted">
                            Track your interview consistency, average scores, and skill readiness.
                        </p>
                    </div>
                </div>
                <span className="vh-dashboard-badge">Live Analytics</span>
            </div>

            <div className="dashboard-stats vh-stats-grid">
                <div className="dashboard-stat vh-stat-box">
                    <div className="vh-stat-top">
                        <span className="vh-stat-icon">
                            <Briefcase size={18} />
                        </span>
                        <span className="vh-stat-tag">Sessions</span>
                    </div>
                    <h3>{totalInterviews}</h3>
                    <p>Total Interviews</p>
                </div>

                <div className="dashboard-stat vh-stat-box highlight">
                    <div className="vh-stat-top">
                        <span className="vh-stat-icon">
                            <Award size={18} />
                        </span>
                        <span className="vh-stat-tag">Performance</span>
                    </div>
                    <h3>{Number(overallScore).toFixed(1)}/10</h3>
                    <p>Average Score</p>
                </div>

                <div className="dashboard-stat vh-stat-box">
                    <div className="vh-stat-top">
                        <span className="vh-stat-icon">
                            <Target size={18} />
                        </span>
                        <span className="vh-stat-tag">Readiness</span>
                    </div>
                    <h3>{Number(skillCoverage).toFixed(1)}%</h3>
                    <p>Skill Coverage</p>
                </div>
            </div>

            <div className="vh-history-section">
                <div className="vh-history-header">
                    <h3>
                        <History size={18} />
                        Interview History
                    </h3>
                    <span className="vh-muted">
                        {history.length} {history.length === 1 ? "session" : "sessions"} recorded
                    </span>
                </div>

                {history.length === 0 ? (
                    <div className="vh-empty-history">
                        <CheckCircle2 size={22} />
                        <div>
                            <strong>No completed interviews yet</strong>
                            <p>
                                Configure a role below and complete your first voice session to
                                populate your history.
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="interview-history vh-history-list">
                        {history.map((interview) => {
                            const report = interview.report || {};
                            const score = Number(report.overall_score ?? 0).toFixed(1);

                            return (
                                <div
                                    className="history-item vh-history-row"
                                    key={interview._id}
                                >
                                    <div className="vh-history-info">
                                        <strong>
                                            {interview.role || report.role || "Interview"}
                                        </strong>

                                        <p>
                                            <span className="vh-diff-pill">
                                                {interview.difficulty || "Standard"}
                                            </span>
                                            <span className="vh-date-meta">
                                                <Calendar size={12} />
                                                {interview.created_at
                                                    ? new Date(
                                                          interview.created_at
                                                      ).toLocaleDateString()
                                                    : "Date unavailable"}
                                            </span>
                                        </p>
                                    </div>

                                    <div className="vh-history-score">
                                        <strong>{score}/10</strong>
                                        <span>Score</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </section>
    );
}