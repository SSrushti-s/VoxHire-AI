
import { useEffect, useState } from "react";

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
        return <section className="dashboard-card">Loading dashboard...</section>;
    }

    if (error) {
        return (
            <section className="dashboard-card">
                <h2>Career Dashboard</h2>
                <p>{error}</p>
            </section>
        );
    }

    const totalInterviews = summary?.total_interviews ?? 0;
    const overallScore = summary?.overall_score ?? 0;
    const skillCoverage = summary?.skill_coverage ?? 0;

    return (
        <section className="dashboard-card">
            <h2>📊 Your Career Dashboard</h2>

            <div className="dashboard-stats">
                <div className="dashboard-stat">
                    <h3>{totalInterviews}</h3>
                    <p>Total Interviews</p>
                </div>

                <div className="dashboard-stat">
                    <h3>{Number(overallScore).toFixed(1)}/10</h3>
                    <p>Average Score</p>
                </div>

                <div className="dashboard-stat">
                    <h3>{Number(skillCoverage).toFixed(1)}%</h3>
                    <p>Skill Coverage</p>
                </div>
            </div>

            <h3>Interview History</h3>

            {history.length === 0 ? (
                <p>You haven't completed any interviews yet.</p>
            ) : (
                <div className="interview-history">
                    {history.map(interview => {
                        const report = interview.report || {};

                        return (
                            <div
                                className="history-item"
                                key={interview._id}
                            >
                                <div>
                                    <strong>
                                        {interview.role || report.role || "Interview"}
                                    </strong>

                                    <p>
                                        {interview.difficulty || "N/A"}
                                        {" · "}
                                        {interview.created_at
                                            ? new Date(interview.created_at).toLocaleDateString()
                                            : "Date unavailable"}
                                    </p>
                                </div>

                                <strong>
                                    {Number(report.overall_score ?? 0).toFixed(1)}/10
                                </strong>
                            </div>
                        );
                    })}
                </div>
            )}
        </section>
    );
}
