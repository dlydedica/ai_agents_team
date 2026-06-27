"""
Дашборд статуса задач AI Agents Team.

Запуск:
    python app.py

Откройте в браузере: http://localhost:8000
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server"))
from task_store import get_all_tasks, STORAGE_DIR

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="AI DevCorp Dashboard")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

DEPARTMENT_EMOJI = {
    "product": "🏭", "architecture": "🏗️", "development": "💻",
    "qa": "🧪", "devops": "⚙️", "design": "🎨", "docs": "📖",
    "hr": "👥", "security": "🛡️", "data": "📊", "rd": "🔬",
    "legal": "⚖️", "marketing": "📣",
}

DEPARTMENT_LABELS = {
    "product": "Product", "architecture": "Architecture",
    "development": "Development", "qa": "QA",
    "devops": "DevOps", "design": "Design",
    "docs": "Docs", "hr": "HR",
    "security": "Security", "data": "Data",
    "rd": "R&D", "legal": "Legal",
    "marketing": "Marketing",
}

STATUS_COLORS = {
    "planned": "#6b7280",
    "in_progress": "#3b82f6",
    "completed": "#10b981",
    "escalated": "#ef4444",
}


def load_data() -> dict:
    """Загрузить данные задач и статус отделов."""
    tasks = get_all_tasks()
    completed_tasks = [t for t in tasks.values() if t.get("status") == "completed"]

    # Тренды
    total_departments_used = set()
    total_events = 0
    for t in tasks.values():
        total_departments_used.update(t.get("departments_plan", []))
        total_events += len(t.get("events", []))

    # Per-department KPI
    dept_kpi = {}
    for dept_id in DEPARTMENT_EMOJI:
        assigned = sum(1 for t in tasks.values() if dept_id in t.get("departments_plan", []))
        completed = sum(1 for t in tasks.values() if dept_id in t.get("departments_completed", []))
        escalated = sum(1 for t in tasks.values()
                        if t.get("status") == "escalated"
                        and dept_id in t.get("departments_plan", []))
        success_rate = round((completed / max(assigned, 1)) * 100)
        dept_kpi[dept_id] = {
            "emoji": DEPARTMENT_EMOJI.get(dept_id, "📁"),
            "label": DEPARTMENT_LABELS.get(dept_id, dept_id),
            "assigned": assigned,
            "completed": completed,
            "escalated": escalated,
            "success_rate": success_rate,
        }

    dept_completion_rank = sorted(
        [
            {
                "id": dept_id,
                "emoji": DEPARTMENT_EMOJI.get(dept_id, "📁"),
                "label": DEPARTMENT_LABELS.get(dept_id, dept_id),
                "count": sum(
                    1 for t in tasks.values()
                    if dept_id in t.get("departments_completed", [])
                ),
            }
            for dept_id in DEPARTMENT_EMOJI
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    return {
        "tasks": tasks,
        "departments": [
            {
                "id": dept_id,
                "emoji": DEPARTMENT_EMOJI.get(dept_id, "📁"),
                "label": DEPARTMENT_LABELS.get(dept_id, dept_id),
                "active_count": sum(
                    1 for t in tasks.values()
                    if t.get("current_department") == dept_id
                    and t.get("status") == "in_progress"
                ),
                "completed_count": sum(
                    1 for t in tasks.values()
                    if dept_id in t.get("departments_completed", [])
                ),
            }
            for dept_id in DEPARTMENT_EMOJI
        ],
        "stats": {
            "total": len(tasks),
            "active": sum(1 for t in tasks.values() if t.get("status") == "in_progress"),
            "completed": len(completed_tasks),
            "planned": sum(1 for t in tasks.values() if t.get("status") == "planned"),
            "escalated": sum(1 for t in tasks.values() if t.get("status") == "escalated"),
        },
        "trends": {
            "total_completed": len(completed_tasks),
            "total_events_logged": total_events,
            "unique_departments_used": len(total_departments_used),
            "top_departments": dept_completion_rank[:5],
            "avg_departments_per_task": round(
                sum(len(t.get("departments_plan", [])) for t in tasks.values()) / max(len(tasks), 1), 1
            ),
        },
        "dept_kpi": dept_kpi,
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    data = load_data()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            **data,
            "DEPARTMENT_EMOJI": DEPARTMENT_EMOJI,
            "DEPARTMENT_LABELS": DEPARTMENT_LABELS,
        },
    )


@app.get("/api/tasks")
async def api_tasks():
    return load_data()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
