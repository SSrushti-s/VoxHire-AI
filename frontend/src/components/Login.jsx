
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
        <div className="auth-container">
            <form className="auth-card" onSubmit={handleSubmit}>
                <h1>Welcome back 👋</h1>
                <p>Log in to continue to VoxHire AI.</p>

                <label>Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={event => setEmail(event.target.value)}
                    placeholder="Enter your email"
                    required
                />

                <label>Password</label>
                <input
                    type="password"
                    value={password}
                    onChange={event => setPassword(event.target.value)}
                    placeholder="Enter your password"
                    required
                />

                {error && <p className="auth-error">{error}</p>}

                <button type="submit" disabled={loading}>
                    {loading ? "Logging in..." : "Login"}
                </button>

                <p>
                    Don't have an account?{" "}
                    <button
                        type="button"
                        className="auth-link"
                        onClick={onSwitch}
                    >
                        Sign up
                    </button>
                </p>
            </form>
        </div>
    );
}
