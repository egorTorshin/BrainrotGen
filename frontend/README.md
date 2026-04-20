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
- `validators.py`: Pure helpers for input validation and formatting.
- `tests/`: Unit + end-to-end tests (see below).

## Testing

The suite combines pure-Python unit tests with end-to-end tests driven by
Streamlit's official [`AppTest`](https://docs.streamlit.io/develop/api-reference/app-testing)
harness (no browser required).

Run everything:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=. --cov-report=term-missing
```

| Test file | Scope |
|-----------|-------|
| `tests/test_duration.py` | Unit tests for quota duration estimation helpers |
| `tests/test_validators.py` | Unit tests for username / password / mm:ss helpers |
| `tests/test_api.py` | HTTP contract tests for `api.py` using `responses` |
| `tests/test_state.py` | Session-state behaviour via AppTest harness |
| `tests/test_e2e_app.py` | Full UI flows (login → generate → preview) via AppTest with mocked backend |

## UI Flow

1. **Authentication**: User logs in or registers to receive a JWT.
2. **Dashboard**: User enters text and selects parameters.
   - The UI provides an "Estimated Duration" hint based on text length.
3. **Queueing**: Upon submission, the job is enqueued in the backend.
4. **Polling**: The "Preview" page polls the backend every 2 seconds until the job is `done` or `failed`.
5. **Result**: Once `done`, the video is loaded for playback and download.
