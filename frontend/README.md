# BrainrotGen Frontend

The frontend is a Streamlit-based web application providing a user interface for the BrainrotGen video generation system.

## Features

- **User Authentication**: Login and Registration (JWT-based).
- **Video Generation Interface**: Text input, voice selection, and background style choice.
- **Real-time Quota Dashboard**: Visual representation of daily consumption and limits.
- **Job Polling & Preview**: Automatic status updates while processing and in-browser video preview.
- **Video Downloads**: Download the final `.mp4` directly from the dashboard.

## Tech Stack

- **Framework**: [Streamlit](https://streamlit.io/)
- **API Communication**: `requests` (connecting to the FastAPI backend)
- **State Management**: Streamlit `session_state`
- **Dependency Management**: Poetry

## Quickstart

### Local Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run the application:
   ```bash
   poetry run streamlit run app.py
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Base URL of the BrainrotGen Backend API | `http://localhost:8000/api/v1` |

## Project Structure

- `app.py`: Main application entry point and UI layout.
- `api.py`: Backend integration layer using `requests`.
- `state.py`: Authentication and navigation state management.
- `duration.py`: UI-side duration estimation (matches backend logic).

## UI Flow

1. **Authentication**: User logs in or registers to receive a JWT.
2. **Dashboard**: User enters text and selects parameters.
   - The UI provides an "Estimated Duration" hint based on text length.
3. **Queueing**: Upon submission, the job is enqueued in the backend.
4. **Polling**: The "Preview" page polls the backend every 2 seconds until the job is `done` or `failed`.
5. **Result**: Once `done`, the video is loaded for playback and download.
