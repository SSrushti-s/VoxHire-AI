
import { useState } from "react";
import { signupUser } from "../services/api";

export default function Signup({ onSuccess, onSwitch }) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(event) {
        event.preventDefault();

        try {
            setLoading(true);
            setError("");

            const result = await signupUser(
                name,
                email,
                password
            );

            onSuccess(result.user);

        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <section className="auth-form-panel auth-signup-panel">
            <div className="auth-form-wrapper">

                <div className="auth-heading">
                    <span className="auth-heading-label">
                        GET STARTED
                    </span>

                    <h2>Create your account</h2>

                    <p>
                        Start preparing for your dream career today.
                    </p>
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>

                    <div className="auth-field">
                        <label htmlFor="signup-name">
                            Full name
                        </label>

                        <input
                            id="signup-name"
                            type="text"
                            value={name}
                            onChange={event => setName(event.target.value)}
                            placeholder="Enter your full name"
                            minLength={2}
                            maxLength={80}
                            autoComplete="name"
                            required
                        />
                    </div>

                    <div className="auth-field">
                        <label htmlFor="signup-email">
                            Email address
                        </label>

                        <input
                            id="signup-email"
                            type="email"
                            value={email}
                            onChange={event => setEmail(event.target.value)}
                            placeholder="you@example.com"
                            autoComplete="email"
                            required
                        />
                    </div>

                    <div className="auth-field">
                        <label htmlFor="signup-password">
                            Password
                        </label>

                        <input
                            id="signup-password"
                            type="password"
                            value={password}
                            onChange={event => setPassword(event.target.value)}
                            placeholder="At least 8 characters"
                            minLength={8}
                            maxLength={128}
                            autoComplete="new-password"
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
                        {loading ? "Creating account..." : "Create account"}
                        {!loading && <span>→</span>}
                    </button>

                </form>

                <div className="auth-switch">
                    Already have an account?

                    <button
                        type="button"
                        className="auth-link"
                        onClick={onSwitch}
                    >
                        Login
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
