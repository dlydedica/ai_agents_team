#!/usr/bin/env python3
"""
👥 HR Engine — реальное развитие команды AI DevCorp.

Анализирует выполненные задачи, оценивает загрузку отделов,
обновляет матрицу компетенций и профили сотрудников.
"""

import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

# Добавляем mcp-server в путь — поднимаемся до корня проекта
_SCRIPT_DIR = Path(__file__).resolve().parent  # departments/hr/
_REPO_DIR = _SCRIPT_DIR.parent.parent  # корень проекта
sys.path.insert(0, str(_REPO_DIR / "mcp-server"))
from task_store import get_all_tasks

REPO_DIR = _REPO_DIR
HR_DIR = REPO_DIR / "docs" / "hr"
COMPETENCY_FILE = REPO_DIR / "docs" / "competency_matrix.md"
EMPLOYEES_FILE = REPO_DIR / "docs" / "employee_profiles.md"
DEPT_DIR = REPO_DIR / "departments"

DEPARTMENT_EMOJI = {
    "product": "🏭", "architecture": "🏗️", "development": "💻",
    "qa": "🧪", "devops": "⚙️", "design": "🎨", "docs": "📖",
    "hr": "👥", "security": "🛡️", "data": "📊", "rd": "🔬",
    "legal": "⚖️", "marketing": "📣",
}


def analyze():
    """Главный анализ: задачи → отчёты → обновления."""
    tasks = get_all_tasks()
    completed = [t for t in tasks.values() if t.get("status") == "completed"]
    active = [t for t in tasks.values() if t.get("status") == "in_progress"]
    escalated = [t for t in tasks.values() if t.get("status") == "escalated"]

    print(f"\n{'='*60}")
    print(f"👥 HR — Анализ команды")
    print(f"{'='*60}")
    print(f"   Всего задач: {len(tasks)}")
    print(f"   Завершено: {len(completed)}")
    print(f"   Активно: {len(active)}")
    print(f"   Эскалировано: {len(escalated)}")
    print()

    # Анализ загрузки отделов
    _analyze_workload(tasks)

    # Анализ ошибок
    _analyze_errors(tasks)

    # Генерация отчёта
    report = _generate_report(tasks, completed, active, escalated)
    print(f"\n📄 Отчёт сохранён: docs/hr/latest-report.md")
    print(f"{'='*60}\n")

    return report


def _analyze_workload(tasks):
    """Проанализировать загрузку и выявить узкие места."""
    dept_stats = {}
    for t in tasks.values():
        for dept in t.get("departments_plan", []):
            if dept not in dept_stats:
                dept_stats[dept] = {"assigned": 0, "completed": 0}
            dept_stats[dept]["assigned"] += 1
        for dept in t.get("departments_completed", []):
            if dept in dept_stats:
                dept_stats[dept]["completed"] += 1

    print("📊 Загрузка отделов:")
    print(f"   {'Отдел':<20} {'Назначено':<12} {'Завершено':<12} {'Загрузка':<10}")
    print(f"   {'─'*54}")
    for dept, stats in sorted(dept_stats.items(), key=lambda x: x[1]["assigned"], reverse=True):
        load = (stats["completed"] / max(stats["assigned"], 1)) * 100
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        bar = "█" * int(load / 10) + "░" * (10 - int(load / 10))
        print(f"   {emoji} {dept:<17} {stats['assigned']:<12} {stats['completed']:<12} {bar} {load:.0f}%")

    # Выявление узких мест
    overloaded = [d for d, s in dept_stats.items() if s["assigned"] > 0 and s["completed"] / max(s["assigned"], 1) < 0.5]
    if overloaded:
        print(f"\n⚠️  Узкие места (завершено <50% назначений):")
        for d in overloaded:
            print(f"   {DEPARTMENT_EMOJI.get(d, '📁')} {d.capitalize()}")
    print()


def _analyze_errors(tasks):
    """Проанализировать ошибки и эскалации."""
    escalated = [t for t in tasks.values() if t.get("status") == "escalated"]
    if escalated:
        print(f"🚨 Эскалированные задачи ({len(escalated)}):")
        for t in escalated:
            print(f"   • {t.get('title', 'Без названия')} ({t.get('id')})")
        print()


def _generate_report(tasks, completed, active, escalated):
    """Сгенерировать markdown-отчёт."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_path = HR_DIR / "latest-report.md"

    # Собираем статистику по отделам
    dept_rows = []
    dept_stats = {}
    for t in tasks.values():
        for dept in t.get("departments_plan", []):
            dept_stats.setdefault(dept, {"tasks": 0, "completed": 0, "errors": 0})
            dept_stats[dept]["tasks"] += 1
        for dept in t.get("departments_completed", []):
            if dept in dept_stats:
                dept_stats[dept]["completed"] += 1
        if t.get("status") == "escalated":
            for dept in t.get("departments_plan", []):
                if dept in dept_stats:
                    dept_stats[dept]["errors"] += 1

    for dept, stats in sorted(dept_stats.items(), key=lambda x: x[1]["tasks"], reverse=True):
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        load = f"{stats['completed']}/{stats['tasks']}"
        dept_rows.append(f"| {emoji} {dept.capitalize()} | {stats['tasks']} | {stats['completed']} | {stats['errors']} | {load} |")

    content = f"""# 👥 HR Отчёт — Performance Review

**Дата:** {now}
**Всего задач:** {len(tasks)}
**Завершено:** {len(completed)} | **Активно:** {len(active)} | **Эскалировано:** {len(escalated)}

---

## Загрузка отделов

| Отдел | Задач | Завершено | Ошибок | Прогресс |
|-------|------|-----------|--------|----------|
{chr(10).join(dept_rows)}

---

## Рекомендации

"""

    # Генерируем рекомендации на основе данных
    recommendations = []

    # Если много задач — нужен новый сотрудник
    for dept, stats in sorted(dept_stats.items(), key=lambda x: x[1]["tasks"], reverse=True):
        if stats["tasks"] >= 5 and stats["completed"] / max(stats["tasks"], 1) < 0.6:
            recommendations.append(
                f"- 🔴 **{dept.capitalize()}** перегружен ({stats['tasks']} задач, завершено {stats['completed']}). "
                f"Рекомендуется нанять Middle+ специалиста."
            )
        elif stats["tasks"] >= 3 and stats["errors"] > 0:
            recommendations.append(
                f"- 🟡 **{dept.capitalize()}** допускает ошибки ({stats['errors']} эскалаций). "
                f"Рекомендуется code review и доп. обучение."
            )

    if not recommendations:
        recommendations.append("- ✅ Команда работает стабильно. Продолжать мониторинг.")

    content += "\n".join(recommendations) + "\n"

    # Добавляем детали по задачам
    content += f"""

---

## Последние задачи

| Задача | Статус | Отделы |
|--------|--------|--------|
"""
    for t in sorted(tasks.values(), key=lambda x: x.get("created_at", ""), reverse=True)[:10]:
        status_emoji = {"completed": "✅", "in_progress": "🔄", "planned": "📋", "escalated": "🚨"}.get(t.get("status", ""), "❓")
        depts = ", ".join(t.get("departments_plan", []))
        content += f"| {status_emoji} {t.get('title', '?')} | {t.get('status', '?')} | {depts} |\n"

    HR_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def update_competency(dept: str, skill: str, grade: str):
    """Обновить матрицу компетенций — добавить скил отделу."""
    if not COMPETENCY_FILE.exists():
        print(f"❌ Файл {COMPETENCY_FILE} не найден")
        return

    content = COMPETENCY_FILE.read_text(encoding="utf-8")
    header = f"## {DEPARTMENT_EMOJI.get(dept, '📁')} {dept.capitalize()}"
    if header not in content:
        print(f"❌ Отдел {dept} не найден в матрице")
        return

    # Добавляем скил в конец секции отдела
    new_skill = f"- {skill} ({grade})"
    sections = content.split(f"\n## ")
    for i, section in enumerate(sections):
        if section.startswith(f"{DEPARTMENT_EMOJI.get(dept, '📁')} {dept.capitalize()}"):
            # Добавляем в секцию перед следующим ##
            lines = section.split("\n")
            # Ищем конец таблицы или списка
            insert_pos = len(lines) - 1
            for j in range(len(lines) - 1, 0, -1):
                if lines[j].strip().startswith("|") or lines[j].strip().startswith("-"):
                    insert_pos = j + 1
                    break
            lines.insert(insert_pos, new_skill)
            sections[i] = "\n".join(lines)
            break

    new_content = "\n## ".join(sections)
    COMPETENCY_FILE.write_text(new_content, encoding="utf-8")
    print(f"✅ Добавлен скил '{skill}' ({grade}) в отдел {dept.capitalize()}")


def add_employee(name: str, role: str, grade: str, dept: str, skills: str = ""):
    """Добавить нового сотрудника в профили."""
    if not EMPLOYEES_FILE.exists():
        print(f"❌ Файл {EMPLOYEES_FILE} не найден")
        return

    content = EMPLOYEES_FILE.read_text(encoding="utf-8")
    header = f"## {DEPARTMENT_EMOJI.get(dept, '📁')} {dept.capitalize()}"

    if header not in content:
        print(f"❌ Отдел {dept} не найден в профилях")
        return

    new_line = f"| 👤 **{name}** | {role} | {grade} | {skills} |"
    # Вставляем после заголовка таблицы
    sections = content.split(f"\n## ")
    for i, section in enumerate(sections):
        if section.startswith(f"{DEPARTMENT_EMOJI.get(dept, '📁')} {dept.capitalize()}"):
            lines = section.split("\n")
            # Находим последнюю строку таблицы
            for j in range(len(lines) - 1, 0, -1):
                if lines[j].strip().startswith("|"):
                    lines.insert(j + 1, new_line)
                    break
            sections[i] = "\n".join(lines)
            break

    new_content = "\n## ".join(sections)
    EMPLOYEES_FILE.write_text(new_content, encoding="utf-8")
    print(f"✅ Добавлен сотрудник {name} ({role}, {grade}) в {dept.capitalize()}")


def promote_employee(name: str, new_grade: str):
    """Повысить грейд сотрудника."""
    if not EMPLOYEES_FILE.exists():
        return

    content = EMPLOYEES_FILE.read_text(encoding="utf-8")
    old_line_pattern = f"**{name}**"
    if old_line_pattern not in content:
        print(f"❌ Сотрудник {name} не найден")
        return

    # Заменяем грейд в строке с сотрудником
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if f"**{name}**" in line:
            # Формат: | 👤 **Name** | Role | Grade | Skills |
            parts = line.split("|")
            if len(parts) >= 4:
                parts[3] = f" {new_grade} "
                lines[i] = "|".join(parts)
                print(f"✅ {name} повышен до {new_grade}")
                break

    EMPLOYEES_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    analyze()
