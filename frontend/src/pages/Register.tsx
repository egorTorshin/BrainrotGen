import { useState } from "react";
import { register } from "../api";
import "./Register.css";

export default function Register() {
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
      const data = await register(username, password);
      localStorage.setItem("access_token", data.access_token);
    } catch (err) {
        console.error(err);
      setError("Registration failed");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
        <h2>Register</h2>
            <div className="input_container">
                <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
                <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
                {error && <p style={{ color: "red" }}>{error}</p>}
                <button type="submit">Register</button>
            </div>
        </form>
  );
}