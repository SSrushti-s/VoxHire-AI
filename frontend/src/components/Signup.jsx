
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
        <div className="auth-container">
            <form className="auth-card" onSubmit={handleSubmit}>
                <h1>Create your account 🚀</h1>
                <p>Start practicing interviews with VoxHire AI.</p>

                <label>Full name</label>
                <input
                    type="text"
                    value={name}
                    onChange={event => setName(event.target.value)}
                    placeholder="Enter your name"
                    minLength={2}
                    maxLength={80}
                    required
                />

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
                    placeholder="At least 8 characters"
                    minLength={8}
                    maxLength={128}
                    required
                />

                {error && <p className="auth-error">{error}</p>}

                <button type="submit" disabled={loading}>
                    {loading ? "Creating account..." : "Sign up"}
                </button>

                <p>
                    Already have an account?{" "}
                    <button
                        type="button"
                        className="auth-link"
                        onClick={onSwitch}
                    >
                        Login
                    </button>
                </p>
            </form>
        </div>
    );
}
