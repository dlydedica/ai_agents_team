"""
Хранилище состояния задач для MCP-сервера.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
try:
    import portalocker
except ImportError:
    portalocker = None


STORAGE_DIR = Path(__file__).parent / "data"
TASKS_FILE = STORAGE_DIR / "tasks.json"
LOCK_FILE = STORAGE_DIR / "tasks.lock"


def _ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("{}", encoding="utf-8")


def _acquire_lock():
    """Блокировка файла для предотвращения race condition."""
    if portalocker:
        lock = open(LOCK_FILE, "a")
        portalocker.lock(lock, portalocker.LOCK_EX)
        return lock
    return None


def _release_lock(lock):
    if lock:
        portalocker.unlock(lock)
        lock.close()


def _load_tasks() -> dict:
    _ensure_storage()
    try:
        data = TASKS_FILE.read_text(encoding="utf-8")
        if not data.strip():
            return {}
        return json.loads(data)
    except (json.JSONDecodeError, FileNotFoundError):
        # Восстанавливаем пустое хранилище при повреждении
        backup = TASKS_FILE.with_suffix(".json.bak")
        if backup.exists():
            try:
                return json.loads(backup.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}


def _save_tasks(tasks: dict):
    _ensure_storage()
    # Backup перед записью
    if TASKS_FILE.exists():
        import shutil
        shutil.copy2(TASKS_FILE, TASKS_FILE.with_suffix(".json.bak"))
    TASKS_FILE.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _with_lock(func):
    """Декоратор для выполнения функции с файловой блокировкой."""
    def wrapper(*args, **kwargs):
        lock = _acquire_lock()
        try:
            return func(*args, **kwargs)
        finally:
            _release_lock(lock)
    return wrapper


_VALID_DEPARTMENTS = {
    "product", "architecture", "development", "qa", "devops",
    "design", "docs", "hr", "security", "data", "rd", "legal", "marketing",
}


def _validate_department(dept: str) -> bool:
    return dept in _VALID_DEPARTMENTS


@_with_lock
def create_task(title: str, departments: list[str], description: str = "") -> dict:
    if not title or not title.strip():
        return {"error": "Название задачи не может быть пустым"}

    invalid_depts = [d for d in departments if not _validate_department(d)]
    if invalid_depts:
        return {"error": f"Неизвестные отделы: {', '.join(invalid_depts)}"}

    tasks = _load_tasks()
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": task_id,
        "title": title.strip(),
        "description": description.strip(),
        "status": "planned",
        "current_department": None,
        "departments_plan": list(departments),
        "departments_completed": [],
        "artifacts": {},
        "events": [{"time": now, "type": "task.created", "detail": title.strip()}],
        "created_at": now,
        "updated_at": now,
    }
    tasks[task_id] = task
    _save_tasks(tasks)
    return task


@_with_lock
def assign_to_department(task_id: str, department: str) -> Optional[dict]:
    if not _validate_department(department):
        return {"error": f"Неизвестный отдел: {department}"}

    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}

    if department not in task["departments_plan"]:
        return {"error": f"Отдел {department} не в плане задачи {task_id}"}

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


@_with_lock
def complete_department(task_id: str, department: str, artifacts: dict = None) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}

    if department not in task["departments_plan"]:
        return {"error": f"Отдел {department} не в плане задачи"}

    if department in task["departments_completed"]:
        return {"error": f"Отдел {department} уже завершил работу"}

    if department != task.get("current_department"):
        return {"error": f"Отдел {department} не назначен на задачу (текущий: {task.get('current_department')})"}

    task["departments_completed"].append(department)
    if artifacts:
        task["artifacts"].update(artifacts)

    task["current_department"] = None
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "department.completed",
        "detail": f"Отдел завершил: {department}",
    })

    if set(task["departments_completed"]) == set(task["departments_plan"]):
        task["status"] = "completed"
        task["current_department"] = None
    else:
        # Автоматически назначаем следующий отдел из плана
        for dept in task["departments_plan"]:
            if dept not in task["departments_completed"]:
                task["current_department"] = dept
                break
    _save_tasks(tasks)
    return task


@_with_lock
def handoff(task_id: str, from_dept: str, to_dept: str, artifacts: dict = None) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}

    if not _validate_department(from_dept) or not _validate_department(to_dept):
        return {"error": "Неизвестный отдел"}

    if from_dept not in task["departments_plan"]:
        return {"error": f"Отдел {from_dept} не в плане задачи"}

    if to_dept not in task["departments_plan"]:
        return {"error": f"Отдел {to_dept} не в плане задачи"}

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


def get_task_timeline(task_id: str) -> Optional[list]:
    """Получить хронологию событий задачи."""
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return None
    return task.get("events", [])


def list_active() -> list[dict]:
    tasks = _load_tasks()
    return [t for t in tasks.values() if t["status"] in ("planned", "in_progress")]


def get_all_tasks() -> dict:
    """Получить все задачи (публичное API для дашборда)."""
    return _load_tasks()


@_with_lock
def log_event(task_id: str, event_type: str, detail: str) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}
    now = datetime.now(timezone.utc).isoformat()
    task["updated_at"] = now
    task["events"].append({"time": now, "type": event_type, "detail": detail})
    # Ограничиваем количество событий (храним последние 100)
    if len(task["events"]) > 100:
        task["events"] = task["events"][-100:]
    _save_tasks(tasks)
    return task


@_with_lock
def escalate(task_id: str, reason: str) -> Optional[dict]:
    tasks = _load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}
    task["status"] = "escalated"
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["events"].append({
        "time": task["updated_at"],
        "type": "escalation",
        "detail": f"🚨 Эскалация: {reason}",
    })
    _save_tasks(tasks)
    return task
