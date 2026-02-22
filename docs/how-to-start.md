# How to Start the Server

## Prerequisites

- Python 3.11+ with `uv` package manager
- Node.js with `pnpm`

## Backend Server

```bash
cd backend

# Install dependencies
uv pip install -e ".[dev,server]" --system

# Start the server (default port 9000)
python -m server

# Start with custom port
python -m server --port 8080
# or
MAHJONG_PORT=8080 python -m server
```

The backend runs a FastAPI + Uvicorn WebSocket server on `http://127.0.0.1:9000`.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/history` | Game history |
| `GET /api/elo` | ELO history |
| `WebSocket /ws` | Game WebSocket |

## Frontend (Web Dev Mode)

```bash
cd frontend

# Install dependencies
pnpm install

# Start Vite dev server (http://localhost:5173)
pnpm dev
```

> Note: Requires the backend server running separately.

## Frontend (Electron Desktop App)

### Development

```bash
# Terminal 1 - Start backend
cd backend
python -m server

# Terminal 2 - Build frontend and launch Electron
cd frontend
pnpm electron:dev
```

### Production Build

```bash
cd frontend
pnpm electron:build   # Creates installer in release/ folder
```

> The Electron app automatically spawns and manages the backend server.

## Running Tests

### Backend

```bash
cd backend

# All tests
uv run pytest -v

# Single test file
uv run pytest tests/test_scorer.py -v

# Integration test (1000 AI games)
uv run pytest tests/test_integration.py -v -s

# Coverage gate (CI threshold: >=85%)
uv run pytest --cov=engine --cov=ai --cov-fail-under=85 --ignore=tests/test_integration.py -q
```

### Frontend

```bash
cd frontend

pnpm test          # Run tests once
pnpm test:watch    # Run tests in watch mode
```
