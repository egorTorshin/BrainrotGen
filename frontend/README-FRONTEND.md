# BrainrotGen Frontend — Architecture
## 1. Overview
Frontend is a client application for interacting with the video generation system.Main responsibilities:
- user text input
- selection of generation parameters
- sending requests to backend
- displaying job status
- preview and download of results

Built with React and TypeScript, communicating via HTTP API.

## 2. Technology Stack
React, TypeScript, Vite, Fetch API

## 3. UI Architecture
### Two-screen MVP:
**Generate Screen:**
- text input
- voice/background selection
- request submission

**Preview Screen:**
- job status polling
- status display
- video preview
- download option

## 4. State Management
Managed via React `useState`: text, voice, background, jobId, status, url

## 5. API Integration
`POST /generate` → returns job_id

`GET /status/{job_id}` → returns status and optional video URL

## 6. Job Flow
```
User input → create job → receive job_id → poll status → display result
```

## 7. Styling
Global CSS with variables, dark/light theme, flexbox layout.

## 8. Build & Run
**For development mode:**
```
npm run dev
```

**Production mode:**
```
npm run build
npm run preview
```