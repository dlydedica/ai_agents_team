#!/usr/bin/env python3
"""
👥 HR — Lifecycle: управление жизненным циклом сотрудников.

Статусы:
  active    — работает, участвует в задачах
  paused    — временно неактивен (отпуск, пауза)
  archived  — уволен/выведен из команды

Возможности:
  - Уволить сотрудника (archive) — скилы распределяются между другими
  - Приостановить (pause) — временно исключить из команды
  - Восстановить (resume) — вернуть из паузы
  - Оценить (rate) — выставить рейтинг сотруднику
  - Понизить (demote) — отобрать часть скилов
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

REPO_DIR = Path(__file__).resolve().parent.parent.parent
MEMBERS_DIR = REPO_DIR / ".github" / "agents" / "members"
HR_DATA_DIR = REPO_DIR / "docs" / "hr"
STATUS_FILE = HR_DATA_DIR / "agent_status.json"

# Статусы сотрудников
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_ARCHIVED = "archived"

HR_EMOJI = "👥"

# Данные о статусах
def _load_statuses() -> dict:
    """Загружает статусы всех сотрудников."""
    try:
        if STATUS_FILE.exists():
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_statuses(statuses: dict):
    """Сохраняет статусы."""
    HR_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(
        json.dumps(statuses, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_all_members() -> list[dict]:
    """Возвращает всех сотрудников с их статусами и файлами."""
    members = []
    statuses = _load_statuses()

    if not MEMBERS_DIR.exists():
        return members

    for f in sorted(MEMBERS_DIR.glob("*.agent.md")):
        name = f.stem.replace(".agent", "")
        info = statuses.get(name, {
            "status": STATUS_ACTIVE,
            "rating": 50,
            "note": "",
            "updated": datetime.now().isoformat()[:10],
        })
        info["name"] = name
        info["file"] = str(f.relative_to(REPO_DIR))
        # Извлекаем роль
        try:
            for line in f.read_text(encoding="utf-8").split("\n"):
                if line.strip().startswith("# "):
                    info["role"] = line.strip("# ").strip()
                    break
        except Exception:
            info["role"] = name
        members.append(info)

    return members


def set_status(name: str, status: str, note: str = "") -> dict:
    """Устанавливает статус сотрудника.

    Args:
        name: имя сотрудника (без .agent)
        status: active / paused / archived
        note: причина

    Returns:
        dict с результатом
    """
    # Проверяем, что сотрудник существует
    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    if not agent_file.exists():
        return {"error": f"Сотрудник '{name}' не найден"}

    statuses = _load_statuses()
    prev_status = statuses.get(name, {}).get("status", STATUS_ACTIVE)

    statuses[name] = {
        "status": status,
        "rating": statuses.get(name, {}).get("rating", 50),
        "note": note or f"Статус изменён: {prev_status} → {status}",
        "updated": datetime.now().isoformat()[:10],
    }
    _save_statuses(statuses)

    emoji_map = {STATUS_ACTIVE: "✅", STATUS_PAUSED: "⏸️", STATUS_ARCHIVED: "🗄️"}

    return {
        "success": True,
        "name": name,
        "status": status,
        "prev_status": prev_status,
        "note": note,
        "emoji": emoji_map.get(status, "❓"),
    }


def set_rating(name: str, rating: int) -> dict:
    """Выставляет рейтинг сотруднику (0-100).

    Args:
        name: имя сотрудника
        rating: оценка 0-100

    Returns:
        dict с результатом
    """
    if not 0 <= rating <= 100:
        return {"error": "Рейтинг должен быть от 0 до 100"}

    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    if not agent_file.exists():
        return {"error": f"Сотрудник '{name}' не найден"}

    statuses = _load_statuses()
    prev = statuses.get(name, {}).get("rating", 50)

    statuses[name] = {
        "status": statuses.get(name, {}).get("status", STATUS_ACTIVE),
        "rating": rating,
        "note": f"Рейтинг изменён: {prev} → {rating}",
        "updated": datetime.now().isoformat()[:10],
    }
    _save_statuses(statuses)

    return {"success": True, "name": name, "rating": rating, "prev_rating": prev}


def archive_member(name: str, reason: str = "") -> dict:
    """Увольняет сотрудника: архивирует и перераспределяет скилы.

    Args:
        name: имя сотрудника
        reason: причина увольнения

    Returns:
        dict с результатом
    """
    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    if not agent_file.exists():
        return {"error": f"Сотрудник '{name}' не найден"}

    # Извлекаем скилы перед архивацией
    skills = []
    try:
        content = agent_file.read_text(encoding="utf-8")
        in_skills = False
        for line in content.split("\n"):
            if line.strip().startswith("## Скилы"):
                in_skills = True
                continue
            if in_skills and line.strip().startswith("## "):
                break
            if in_skills:
                m = re.match(r'^\s*-\s*`(.+?)`', line.strip())
                if m:
                    skills.append(m.group(1))
    except Exception:
        pass

    # Архивируем — переименовываем файл
    archive_dir = MEMBERS_DIR / ".." / "members_archived"
    archive_path = (REPO_DIR / archive_dir).resolve()
    archive_path.mkdir(parents=True, exist_ok=True)

    # Добавляем дату к имени файла
    date_str = datetime.now().strftime("%Y%m%d")
    archived_name = f"{name}_archived_{date_str}.agent.md"
    archived_file = archive_path / archived_name

    # Переносим файл
    import shutil
    shutil.move(str(agent_file), str(archived_file))

    # Обновляем статус
    note = reason or "Уволен"
    result = set_status(name, STATUS_ARCHIVED, note)

    return {
        "success": True,
        "name": name,
        "archived_file": str(archived_file.relative_to(REPO_DIR)),
        "skills_freed": skills,
        "reason": reason,
    }


def demote_member(name: str, skills_to_remove: list[str] = None) -> dict:
    """Понижает сотрудника: отбирает указанные скилы.

    Если skills_to_remove не указаны — убирает последние 2 скила.

    Args:
        name: имя сотрудника
        skills_to_remove: список скилов для удаления

    Returns:
        dict с результатом
    """
    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    if not agent_file.exists():
        return {"error": f"Сотрудник '{name}' не найден"}

    content = agent_file.read_text(encoding="utf-8")
    removed = []

    if skills_to_remove:
        for s in skills_to_remove:
            if re.search(rf'^\s*-\s*`{re.escape(s)}`', content, re.MULTILINE):
                content = re.sub(
                    rf'^\s*-\s*`{re.escape(s)}`.*\n?',
                    '', content, flags=re.MULTILINE
                )
                removed.append(s)
    else:
        # Убираем последние 2 скила из секции ## Скилы
        lines = content.split("\n")
        in_skills = False
        skill_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith("## Скилы"):
                in_skills = True
                continue
            if in_skills and line.strip().startswith("## "):
                break
            if in_skills and re.match(r'^\s*-\s*`', line.strip()):
                skill_lines.append(i)

        # Удаляем последние 2
        for idx in skill_lines[-2:]:
            m = re.match(r'^\s*-\s*`(.+?)`', lines[idx])
            if m:
                removed.append(m.group(1))
            lines[idx] = ""

        content = "\n".join(line for line in lines if line.strip())

    # Чистим лишние пустые строки
    content = re.sub(r'\n{3,}', '\n\n', content)
    agent_file.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "name": name,
        "removed_skills": removed,
        "remaining": "см. файл",
    }


def get_status_report() -> list[dict]:
    """Возвращает отчёт по всем сотрудникам."""
    members = get_all_members()
    return sorted(members, key=lambda m: (
        {"active": 0, "paused": 1, "archived": 2}.get(m["status"], 3),
        -m.get("rating", 0),
    ))


# CLI
def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(f"\n{HR_EMOJI} HR — Статус сотрудников\n")
        members = get_status_report()
        for m in members:
            s = m["status"]
            emoji = {"active": "✅", "paused": "⏸️", "archived": "🗄️"}.get(s, "❓")
            rating_stars = "⭐" * (m.get("rating", 50) // 20) + "☆" * (5 - m.get("rating", 50) // 20)
            note = m.get("note", "")
            print(f"  {emoji} {m['name']:35s} | {s:10s} | {rating_stars} {m.get('rating', 0):3d}")
            if note:
                print(f"       {note}")
        print()

    elif cmd == "fire":
        if len(sys.argv) < 3:
            print(f"❌ Укажите сотрудника: python hr/lifecycle.py fire <name> [причина]")
            return
        name = sys.argv[2]
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        result = archive_member(name, reason)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Увольнение\n")
            print(f"  🗄️  {result['name']} — уволен")
            print(f"  📄 Архив: {result['archived_file']}")
            if result["skills_freed"]:
                print(f"  🔄 Освобождены скилы: {', '.join(result['skills_freed'])}")
            print()

    elif cmd == "pause":
        if len(sys.argv) < 3:
            print(f"❌ Укажите сотрудника: python hr/lifecycle.py pause <name> [причина]")
            return
        name = sys.argv[2]
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Отправлен в отпуск"
        result = set_status(name, STATUS_PAUSED, reason)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Пауза\n")
            print(f"  ⏸️  {result['name']} — приостановлен")
            print(f"  📝 {result['note']}")
            print(f"  💡 python team.py hr resume {name} — восстановить\n")

    elif cmd == "resume":
        if len(sys.argv) < 3:
            print(f"❌ Укажите сотрудника: python hr/lifecycle.py resume <name>")
            return
        name = sys.argv[2]
        result = set_status(name, STATUS_ACTIVE, "Возвращён в команду")
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Восстановление\n")
            print(f"  ✅ {result['name']} — возвращён в строй\n")

    elif cmd == "rate":
        if len(sys.argv) < 4:
            print(f"❌ Использование: python hr/lifecycle.py rate <name> <0-100>")
            return
        name = sys.argv[2]
        try:
            rating = int(sys.argv[3])
        except ValueError:
            print("❌ Рейтинг должен быть числом от 0 до 100")
            return
        result = set_rating(name, rating)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Оценка\n")
            print(f"  ⭐ {result['name']}: {result['prev_rating']} → {result['rating']}\n")

    elif cmd == "demote":
        if len(sys.argv) < 3:
            print(f"❌ Укажите сотрудника: python hr/lifecycle.py demote <name> [скил...]")
            return
        name = sys.argv[2]
        skills = sys.argv[3:] if len(sys.argv) > 3 else None
        result = demote_member(name, skills)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Понижение\n")
            print(f"  📉 {result['name']}")
            if result["removed_skills"]:
                print(f"  🔄 Отобраны скилы: {', '.join(result['removed_skills'])}")
            print(f"  💡 Освобождённые скилы можно назначить новому сотруднику\n")


if __name__ == "__main__":
    _cli()
