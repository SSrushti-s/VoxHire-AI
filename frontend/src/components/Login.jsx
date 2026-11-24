
import { useState } from "react";
import { loginUser } from "../services/api";

export default function Login({ onSuccess, onSwitch }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(event) {
        event.preventDefault();

        try {
            setLoading(true);
            setError("");

            const result = await loginUser(email, password);
            onSuccess(result.user);

        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <section className="auth-form-panel auth-login-panel">
            <div className="auth-form-wrapper">

                <div className="auth-heading">
                    <span className="auth-heading-label">
                        WELCOME BACK
                    </span>

                    <h2>Welcome back!</h2>

                    <p>
                        Sign in to continue your interview journey.
                    </p>
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>

                    <div className="auth-field">
                        <label htmlFor="login-email">
                            Email address
                        </label>

                        <input
                            id="login-email"
                            type="email"
                            value={email}
                            onChange={event => setEmail(event.target.value)}
                            placeholder="you@example.com"
                            autoComplete="email"
                            required
                        />
                    </div>

                    <div className="auth-field">
                        <label htmlFor="login-password">
                            Password
                        </label>

                        <input
                            id="login-password"
                            type="password"
                            value={password}
                            onChange={event => setPassword(event.target.value)}
                            placeholder="Enter your password"
                            autoComplete="current-password"
                            required
                        />
                    </div>

                    {error && (
                        <p className="auth-error">{error}</p>
                    )}

                    <button
                        type="submit"
                        className="auth-submit"
                        disabled={loading}
                    >
                        {loading ? "Signing in..." : "Login"}
                        {!loading && <span>→</span>}
                    </button>

                </form>

                <div className="auth-switch">
                    Don't have an account?

                    <button
                        type="button"
                        className="auth-link"
                        onClick={onSwitch}
                    >
                        Sign up
                    </button>
                </div>

                <div className="auth-security">
                    <span>✦</span>
                    Your information is securely protected.
                </div>

            </div>
        </section>
    );
}
