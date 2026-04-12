# BrainrotGen API Documentation

This document provides a detailed overview of the BrainrotGen Backend API endpoints, authentication flows, and quota management.

## Base URL
`http://localhost:8000/api/v1`

---

## Authentication

All endpoints (except registration and login) require a **JWT Bearer Token** in the header.

**Header Format:**
```
Authorization: Bearer <your_access_token>
```

### 1. Register User
`POST /auth/register`

Create a new account.

**Request Body:**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `username` | string | Yes | Min 3 chars, max 64. |
| `password` | string | Yes | Min 6 chars. |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "jdoe", "password": "securepass123"}'
```

---

### 2. Login
`POST /auth/login`

Obtain an access token for an existing account.

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "jdoe", "password": "securepass123"}'
```

---

## Quota Management

The system enforces a daily generation limit.

### 3. Get Quota Status
`GET /jobs/quota`

Returns how many seconds of video you can still generate today.

**Response:**
```json
{
  "daily_limit_seconds": 300,
  "used_seconds": 65.2,
  "remaining_seconds": 234.8
}
```

---

## Job Management

### 4. Create Generation Job
`POST /jobs`

Submits text and parameters for video generation.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `text` | string | - | The script for the video (max 5000 chars). |
| `voice` | string | `male` | `male` or `female`. |
| `background` | string | `minecraft` | `minecraft` or `subway`. |

**Error Handling:**
- Returns `429 Too Many Requests` if the estimated video duration exceeds your `remaining_seconds`.

---

### 5. Get Job Status
`GET /jobs/{job_id}`

Track the progress of a generation task.

**Statuses:**
- `queued`: Waiting for an available worker.
- `processing`: Worker is currently running TTS and video assembly.
- `done`: Video is ready for download.
- `failed`: An error occurred during generation (check the `error` field).

---

### 6. Download Result
`GET /jobs/{job_id}/result`

Fetches the final MP4 file.

**Query Parameters:**
- `attachment` (bool): If `true`, triggers a browser download. Default is `false` (inline viewing).

---

## System Health

### 7. Health Check
`GET /health`

Lightweight endpoint to verify service availability.
