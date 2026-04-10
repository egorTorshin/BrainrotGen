const API_URL = "http://127.0.0.1:8000/api/v1";

let token: string | null = null;

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

export async function createJob(data: { text: string, voice: string, background: string }) {
  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error("Failed to create job");
  }

  return res.json();
}

export async function getStatus(jobId: string) {
  const res =  await fetch(`${API_URL}/jobs/${jobId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error("Failed to get job status");
  }

  return res.json();
}