import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setError("");
    if (username.length < 3) {
        setError("Username must be at least 3 characters");
        return;
    }

    if (password.length < 6) {
        setError("Password must be at least 6 characters");
        return;
    }

    try {
      const data = await login(username, password);
      localStorage.setItem("access_token", data.access_token);
      navigate("/");
    } catch (err) {
      setError("Login failed");
    }
  };

  return (
    <>
        <form onSubmit={handleSubmit}>
        <h2>Login</h2>
            <div className="input_container">
                <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
                <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
                {error && <p style={{ color: "red" }}>{error}</p>}
                <button type="submit">Login</button>
                <a href="/register">I don't have an account</a>
            </div>
        </form>
    </>
  );
}