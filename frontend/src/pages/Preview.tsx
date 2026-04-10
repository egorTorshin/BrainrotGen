import { useEffect, useRef, useState } from "react";
import { fetchJobResultObjectUrl, getStatus } from "../api";
import "./Preview.css";

export default function Preview({
  jobId,
  onBack,
}: {
  jobId: string;
  onBack: () => void;
}) {
  const [status, setStatus] = useState("loading");
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await getStatus(jobId);
        setStatus(data.status);

        if (data.status === "done") {
          clearInterval(interval);
          const objectUrl = await fetchJobResultObjectUrl(jobId);
          objectUrlRef.current = objectUrl;
          setUrl(objectUrl);
        }

        if (data.status === "failed") {
          clearInterval(interval);
          setError(data.error ?? "Generation failed");
        }
      } catch (e) {
        clearInterval(interval);
        setError(e instanceof Error ? e.message : "Status request failed");
      }
    }, 2000);

    return () => {
      clearInterval(interval);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [jobId]);

  return (
    <div className="container">
      <header className="header">
        <a onClick={onBack}>← Back</a>
        <h1>Preview</h1>
      </header>

      {status !== "failed" && !error && status === "loading" && (
        <p>Loading...</p>
      )}

      {status !== "failed" &&
        !error &&
        status !== "loading" &&
        status !== "done" && <p>Status: {status}</p>}

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {url && (
        <>
          <video src={url} controls className="video" />
        </>
      )}

      <div className="buttons_container">
        <button
          type="button"
          onClick={() => url && window.open(url, "_blank")}
          disabled={!url}
        >
          Open in new tab
        </button>
      </div>
    </div>
  );
}
