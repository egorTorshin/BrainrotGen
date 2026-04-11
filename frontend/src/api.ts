const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

function authHeader(): Record<string, string> {
  const t = localStorage.getItem("access_token");
  if (!t) return {};
  return { Authorization: `Bearer ${t}` };
}

export async function register(username: string, password: string) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    console.error(data);
    throw new Error("Failed to register");
  }

  return data;
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    throw new Error("Failed to login");
  }
  return res.json();
}

export async function createJob(data: {
  text: string;
  voice: string;
  background: string;
}) {
  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : res.statusText || "Failed to create job",
    );
  }

  return res.json();
}

export async function getStatus(jobId: string) {
  const res = await fetch(`${API_URL}/jobs/${jobId}`, {
    headers: {
      ...authHeader(),
    },
  });

  if (!res.ok) {
    throw new Error("Failed to get job status");
  }

  return res.json();
}

/** Stream video through authenticated API; returns an object URL (caller should revoke). */
export async function fetchJobResultObjectUrl(jobId: string): Promise<string> {
  const res = await fetch(`${API_URL}/jobs/${jobId}/result`, {
    headers: { ...authHeader() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      typeof err.detail === "string" ? err.detail : "Failed to load video",
    );
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
