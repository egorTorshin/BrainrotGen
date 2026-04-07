import { useState } from "react";
import { createJob } from "../api";
import "./Generate.css";

export default function Generate({ onCreated }: { onCreated: (jobId: string) => void }) {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("male");
  const [background, setBackground] = useState("minecraft");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setLoading(true);

    const data = await createJob({ text, voice, background });

    setLoading(false);
    onCreated(data.job_id);
  }

  return (
    <div className="container">
      <h1>BrainrotGen</h1>

      <div className="form">
        <textarea autoFocus placeholder="Enter your text here..." className="text_input"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="select_group">
          <p>Select voice:</p>
          <select value={voice} onChange={(e) => setVoice(e.target.value)}>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>

        <div className="select_group">
          <p>Select background:</p>
          <select value={background} onChange={(e) => setBackground(e.target.value)}>
            <option value="minecraft">Minecraft Parkour</option>
            <option value="subway">Subway Surfers</option>
          </select>
        </div>

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Generating..." : "Generate"}
        </button>
      </div>
    </div>
  );
}
