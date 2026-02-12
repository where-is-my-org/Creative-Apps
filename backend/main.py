import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mcp_client import MCPStdioClient

load_dotenv()

app = FastAPI(title="Recap Storyboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class RecapRequest(BaseModel):
    repo: str = Field(..., examples=["owner/repo"])
    since: str = Field(..., examples=["2025-12-01"])
    until: str = Field(..., examples=["2026-01-31"])
    githubToken: Optional[str] = Field(None, examples=["ghp_example"])


class RecapResponse(BaseModel):
    project: Dict[str, Any]
    range: Dict[str, Any]
    summary: Dict[str, Any]
    chapters: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    metrics: Dict[str, int]
    sourceNotes: List[str]


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def build_summary(prs: list, commits: list, notes: list, since: str, until: str) -> Dict[str, Any]:
    days = (parse_date(until) - parse_date(since)).days + 1
    headline = f"Shipped {len(prs)} PRs and {len(commits)} commits across {days} days."

    highlights = [item.get("title") for item in prs[:2]]
    highlights += [f"Commit: {item.get('message')}" for item in commits[:1]]
    highlights = [item for item in highlights if item]
    if not highlights:
        highlights = ["No major highlights captured yet."]

    risks = [note.get("title") for note in notes if "risk" in note.get("tags", []) or "blocker" in note.get("tags", [])]
    if not risks:
        risks = ["No major risks recorded."]

    next_steps = [note.get("title") for note in notes if "next" in note.get("tags", [])]
    if not next_steps:
        next_steps = ["Pick the next milestone and align on scope.", "Draft the next recap to lock in outcomes."]

    return {"headline": headline, "highlights": highlights, "risks": risks, "next": next_steps}


def build_chapters(prs: list, commits: list, notes: list) -> List[Dict[str, Any]]:
    chapter_one = [
        "Set the product vision and recap goals.",
        f"Opened {len(prs)} pull requests to move work forward.",
        f"Logged {len(commits)} commits for the sprint narrative."
    ]
    chapter_two = [
        "Resolved blockers and clarified integration paths.",
        "Validated the demo flow with stakeholders.",
        "Captured key decisions in recap notes."
    ]
    chapter_three = [
        "Summarized measurable outcomes and wins.",
        "Documented risks and areas to revisit.",
        "Outlined next steps for the next sprint." 
    ]
    return [
        {"title": "Act I: Setting the stage", "beats": chapter_one},
        {"title": "Act II: Turning points", "beats": chapter_two},
        {"title": "Act III: Results and next", "beats": chapter_three}
    ]


def build_timeline(prs: list, commits: list, notes: list) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for pr in prs:
        items.append(
            {
                "date": pr.get("date", ""),
                "title": pr.get("title", "PR update"),
                "detail": pr.get("url", ""),
                "type": "pr"
            }
        )
    for commit in commits:
        items.append(
            {
                "date": commit.get("date", ""),
                "title": commit.get("message", "Commit update"),
                "detail": commit.get("sha", ""),
                "type": "commit"
            }
        )
    for note in notes:
        items.append(
            {
                "date": note.get("date", ""),
                "title": note.get("title", "Note"),
                "detail": note.get("detail", ""),
                "type": "note"
            }
        )
    items.sort(key=lambda item: item.get("date", ""), reverse=True)
    return items[:12]


def build_recap(repo: str, since: str, until: str, github_data: dict, notes_data: dict) -> Dict[str, Any]:
    prs = github_data.get("pull_requests", [])
    commits = github_data.get("commits", [])
    notes = notes_data.get("notes", [])

    summary = build_summary(prs, commits, notes, since, until)
    chapters = build_chapters(prs, commits, notes)
    timeline = build_timeline(prs, commits, notes)

    return {
        "project": {"repo": repo, "title": repo.replace("/", " ")},
        "range": {"since": since, "until": until},
        "summary": summary,
        "chapters": chapters,
        "timeline": timeline,
        "metrics": {"prCount": len(prs), "commitCount": len(commits), "noteCount": len(notes)},
        "sourceNotes": [note.get("title", "") for note in notes]
    }


@app.post("/api/recap", response_model=RecapResponse)
def create_recap(payload: RecapRequest) -> Dict[str, Any]:
    server_cmd = os.getenv("MCP_SERVER_CMD", "python mcp_server.py")
    try:
        with MCPStdioClient(server_cmd) as client:
            github_data = client.call_tool(
                "github_activity",
                {
                    "repo": payload.repo,
                    "since": payload.since,
                    "until": payload.until,
                    "token": payload.githubToken
                }
            )
            notes_data = client.call_tool(
                "local_notes",
                {"since": payload.since, "until": payload.until}
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return build_recap(payload.repo, payload.since, payload.until, github_data, notes_data)
