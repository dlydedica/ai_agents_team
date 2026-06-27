"""
Хранилище состояния задач для MCP-сервера.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


STORAGE_DIR = Path(__file__).parent / "data"
TASKS_FILE = STORAGE_DIR / "tasks.json"


def _ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("{}", encoding="utf-8")


def _load_tasks() -> dict:
    _ensure_storage()
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def _save_tasks(tasks: dict):
    _ensure_storage()
    TASKS_FILE.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def create_task(title: str, departments: list[str], description: str = "") -> dict:
    tasks = _load_tasks()
    task_id = f"task-{len(tasks) + 1:03d}"
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "status": "planned",
        "current_department": None,
        "departments_plan": departments,
        "departments_completed": [],
        "artifacts": {},
        "events": [{"time": now, "type": "task.created", "detail": title}],
        "created_at": now,
        "updated_at": now,
    }
    tasks[task_id] = task
    _save_tasks(tasks)
    return task


def assign_to_department(task_id: str, department: str) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    task["current_department"] = department
    task["status"] = "in_progress"
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "department.assigned",
        "detail": f"Назначено отделу: {department}",
    })
    _save_tasks(tasks)
    return task


def complete_department(task_id: str, department: str, artifacts: dict = None) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    if department not in task["departments_completed"]:
        task["departments_completed"].append(department)
    if artifacts:
        task["artifacts"].update(artifacts)
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "department.completed",
        "detail": f"Отдел завершил: {department}",
    })
    # Если все отделы завершили — задача выполнена
    if set(task["departments_completed"]) == set(task["departments_plan"]):
        task["status"] = "completed"
        task["current_department"] = None
    _save_tasks(tasks)
    return task


def handoff(task_id: str, from_dept: str, to_dept: str, artifacts: dict = None) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    if from_dept not in task["departments_completed"]:
        task["departments_completed"].append(from_dept)
    if artifacts:
        task["artifacts"].update(artifacts)
    task["current_department"] = to_dept
    task["status"] = "in_progress"
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "handoff",
        "detail": f"Handoff: {from_dept} → {to_dept}",
    })
    _save_tasks(tasks)
    return task


def get_task(task_id: str) -> Optional[dict]:
    tasks = _load_tasks()
    return tasks.get(task_id)


def list_active() -> list[dict]:
    tasks = _load_tasks()
    return [t for t in tasks.values() if t["status"] in ("planned", "in_progress")]


def log_event(task_id: str, event_type: str, detail: str) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    now = datetime.now(timezone.utc).isoformat()
    task["updated_at"] = now
    task["events"].append({"time": now, "type": event_type, "detail": detail})
    _save_tasks(tasks)
    return task


def escalate(task_id: str, reason: str) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    task["status"] = "escalated"
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "escalation",
        "detail": f"Эскалация: {reason}",
    })
    _save_tasks(tasks)
    return task
