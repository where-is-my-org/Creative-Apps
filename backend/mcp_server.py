import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

BASE_DIR = Path(__file__).resolve().parent
NOTES_PATH = BASE_DIR / "data" / "notes.json"

TOOLS = [
    {
        "name": "github_activity",
        "description": "Fetch pull requests and commits for a repo in a date range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "since": {"type": "string"},
                "until": {"type": "string"},
                "token": {"type": "string"}
            },
            "required": ["repo", "since", "until"]
        }
    },
    {
        "name": "local_notes",
        "description": "Read local recap notes for a date range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {"type": "string"},
                "until": {"type": "string"}
            },
            "required": ["since", "until"]
        }
    }
]


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def github_headers(token_override: Optional[str] = None) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = token_override or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_pull_requests(repo: str, since: str, until: str, token: Optional[str] = None) -> list:
    query = f"repo:{repo} is:pr created:{since}..{until}"
    url = "https://api.github.com/search/issues"
    response = httpx.get(
        url,
        params={"q": query, "per_page": 20},
        headers=github_headers(token),
        timeout=20
    )
    response.raise_for_status()
    items = response.json().get("items", [])
    results = []
    for item in items:
        results.append(
            {
                "title": item.get("title", "Untitled PR"),
                "url": item.get("html_url", ""),
                "date": item.get("created_at", "")[:10],
                "author": (item.get("user") or {}).get("login", "")
            }
        )
    return results


def fetch_commits(repo: str, since: str, until: str, token: Optional[str] = None) -> list:
    url = f"https://api.github.com/repos/{repo}/commits"
    response = httpx.get(
        url,
        params={"since": f"{since}T00:00:00Z", "until": f"{until}T23:59:59Z", "per_page": 20},
        headers=github_headers(token),
        timeout=20
    )
    response.raise_for_status()
    results = []
    for item in response.json():
        commit = item.get("commit", {})
        author = commit.get("author", {})
        results.append(
            {
                "message": commit.get("message", "").split("\n")[0],
                "sha": item.get("sha", "")[:7],
                "date": (author.get("date") or "")[:10],
                "author": author.get("name", "")
            }
        )
    return results


def fetch_notes(since: str, until: str) -> list:
    if not NOTES_PATH.exists():
        return []
    payload = json.loads(NOTES_PATH.read_text())
    start = parse_date(since)
    end = parse_date(until)
    results = []
    for note in payload:
        try:
            note_date = parse_date(note.get("date", ""))
        except ValueError:
            continue
        if start <= note_date <= end:
            results.append(note)
    return results


def handle_initialize() -> dict:
    return {
        "protocolVersion": "0.1",
        "serverInfo": {"name": "recap-mcp", "version": "0.1.0"},
        "capabilities": {"tools": {}}
    }


def handle_tool_call(name: str, arguments: dict) -> dict:
    if name == "github_activity":
        repo = arguments["repo"]
        since = arguments["since"]
        until = arguments["until"]
        token = arguments.get("token")
        prs = fetch_pull_requests(repo, since, until, token)
        commits = fetch_commits(repo, since, until, token)
        return {"pull_requests": prs, "commits": commits}
    if name == "local_notes":
        return {"notes": fetch_notes(arguments["since"], arguments["until"])}
    raise ValueError(f"Unknown tool: {name}")


def send_message(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        request = json.loads(line)
        method = request.get("method")
        request_id = request.get("id")
        try:
            if method == "initialize":
                result = handle_initialize()
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params") or {}
                result = handle_tool_call(params.get("name", ""), params.get("arguments") or {})
            else:
                raise ValueError("Unsupported method")
            send_message({"jsonrpc": "2.0", "id": request_id, "result": result})
        except Exception as exc:
            send_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": str(exc)}
                }
            )


if __name__ == "__main__":
    main()
