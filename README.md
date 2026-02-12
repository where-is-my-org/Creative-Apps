# Recap Storyboard

Turn GitHub activity and local notes into a narrative recap with chapters, highlights, risks, and a timeline.

## What this project does

- Pulls PRs and commits from GitHub for a date range
- Blends in local notes to capture decisions, risks, and next steps
- Generates a recap payload for a storyboard-style UI

## Architecture

- Backend: FastAPI service that calls a local MCP server over stdio
- MCP server: Fetches GitHub activity and reads local notes
- Frontend: Vite + React UI for generating and viewing the recap

## Project layout

- backend/main.py: FastAPI API
- backend/mcp_server.py: MCP server exposing tools
- backend/mcp_client.py: stdio client for MCP
- backend/data/notes.json: local notes data
- frontend/src: React app

## Requirements

- Python 3.10+
- Node.js 18+

## Setup

Backend dependencies:

- cd backend
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt

Frontend dependencies:

- cd frontend
- npm install

## Run locally

Start the backend (from backend/):

- uvicorn main:app --reload --port 8000

Start the frontend (from frontend/):

- npm run dev

The UI runs at http://localhost:5173 and calls the API at http://localhost:8000.

## Configuration

Environment variables:

- GITHUB_TOKEN (optional): GitHub personal access token for higher rate limits
- MCP_SERVER_CMD (optional): command to start the MCP server, defaults to "python mcp_server.py"
- VITE_API_BASE (optional): base URL for the API, defaults to http://localhost:8000

Create a .env file in backend/ if you want to set GITHUB_TOKEN or MCP_SERVER_CMD.

## API

POST /api/recap

Request body:

- repo: "owner/repo" (required format)
- since: "YYYY-MM-DD"
- until: "YYYY-MM-DD"
- githubToken: optional string

Response includes summary, chapters, timeline, and metrics.

## Local notes format

backend/data/notes.json is an array of items:

- date: "YYYY-MM-DD"
- title: short summary
- detail: longer context
- tags: array of strings, for example: note, decision, risk, blocker, next

Only notes within the requested date range are included in the recap.

## Troubleshooting

- If the frontend cannot reach the API, confirm VITE_API_BASE and that port 8000 is open.
- If GitHub requests fail, set GITHUB_TOKEN to avoid rate limits.

## License

MIT (add or update as needed)
