import { useEffect, useState } from "react";
import { getStatus } from "../api";
import "./Preview.css";

export default function Preview({ jobId, onBack }: { jobId: string; onBack: () => void }) {
  const [status, setStatus] = useState("loading");
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      const data = await getStatus(jobId);

      setStatus(data.status);

      if (data.status === "done" && data.url) {
        setUrl(data.url);
        clearInterval(interval);
      }

      if (data.status === "failed") {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="container">
      <header className="header"> 
        <a onClick={onBack}>← Back</a>
        <h1>Preview</h1>
      </header>

      {status === "loading" && <p>Loading...</p>}

      {url && (
        <>
          <video src={url} controls className="video" />
        </>
      )}

      <div className="buttons_container">
        <button onClick={() => url && window.open(url, "_blank")}>Download</button>
      </div>
    </div>
  );
}