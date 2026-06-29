#!/usr/bin/env python3
"""
👥 HR — Agent Factory: создание, найм, балансировка сотрудников.

Позволяет:
  - Определить, нужен ли новый сотрудник (критерии найма)
  - Создать нового сотрудника (.agent.md файл)
  - Перебалансировать скилы между сотрудниками
  - Отобрать часть скилов у перегруженных в пользу нового
"""

import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
MEMBERS_DIR = REPO_DIR / ".github" / "agents" / "members"
SKILLS_DIR = REPO_DIR / "skills"

HR_EMOJI = "👥"

# Критерии найма нового сотрудника
HIRE_CRITERIA = {
    "max_skills_per_member": 6,     # если у сотрудника >6 — он перегружен
    "max_duplicate_skills": 3,      # если скил дублируется у >3 сотрудников
    "min_optimal_members": 2,       # минимум 2 сотрудника с оптимальным набором
    "uncovered_threshold": 5,       # если >5 скилов без сотрудника
}

AGENT_TEMPLATE = """---
description: "{role} — {description}"
tools: [read, search, edit, execute]
user-invocable: false
---

# {emoji} {role}

Получаешь задачу от Head of {department}.

## Скилы
{skills}

## Что сделать
{responsibilities}

## Выход
{outputs}
"""


def analyze_hiring_need() -> dict:
    """Анализирует, нужен ли новый сотрудник.

    Returns:
        dict с ключами:
          - need_hire: bool
          - reasons: list[str]
          - overloaded: list[dict] — перегруженные сотрудники
          - candidates: list[str] — какие скилы можно отдать новому
    """
    from departments.hr.skill_balance import analyze_balance

    reports = analyze_balance()
    reasons = []
    overloaded = []
    candidates = set()

    for report in reports:
        if not report.members:
            reasons.append(f"Отдел '{report.department}' не имеет сотрудников")
            continue

        # Перегруженные
        for m in report.overloaded:
            overloaded.append({
                "name": m.name,
                "department": report.department,
                "skills": m.skills,
                "skill_count": m.skill_count,
                "excess": m.skill_count - HIRE_CRITERIA["max_skills_per_member"],
            })
            # Какие скилы можно отдать (последние N из списка перегруженного)
            excess = m.skill_count - HIRE_CRITERIA["max_skills_per_member"]
            for s in m.skills[-excess:]:
                candidates.add(s)

        # Дубликаты
        dup_count = len(report.duplicates)
        if dup_count >= HIRE_CRITERIA["max_duplicate_skills"]:
            dup_skills = set(d[0] for d in report.duplicates)
            reasons.append(
                f"Много дубликатов ({dup_count}) в '{report.department}': "
                f"{', '.join(list(dup_skills)[:3])}"
            )
            for d in report.duplicates:
                candidates.add(d[0])

        # Пробелы
        if len(report.gaps) >= HIRE_CRITERIA["uncovered_threshold"]:
            reasons.append(
                f"Непокрытые скилы ({len(report.gaps)}) в '{report.department}': "
                f"{', '.join(report.gaps[:5])}"
            )
            for g in report.gaps:
                candidates.add(g)

    need_hire = bool(overloaded) or len(reasons) > 0

    return {
        "need_hire": need_hire,
        "reasons": reasons,
        "overloaded": overloaded,
        "candidates": sorted(candidates),
    }


def suggest_new_agent() -> dict:
    """Предлагает параметры для нового сотрудника.

    Returns:
        dict: name, role, emoji, department, skills, description
    """
    hire_info = analyze_hiring_need()

    if not hire_info["need_hire"]:
        return {"error": "Новый сотрудник не требуется — баланс в норме"}

    # Определяем отдел для нового сотрудника
    dept_counts = {}
    for o in hire_info["overloaded"]:
        dept_counts[o["department"]] = dept_counts.get(o["department"], 0) + 1

    target_dept = max(dept_counts, key=dept_counts.get) if dept_counts else "development"

    # Определяем специализацию
    candidates = hire_info["candidates"]
    if not candidates:
        candidates = ["general"]

    # Определяем навыки (берём уникальные из candidates)
    skills = list(dict.fromkeys(candidates))[:5]  # макс 5 скилов

    # Генерируем имя и роль
    skill_tags = []
    for s in skills:
        if "flutter" in s or "dart" in s:
            skill_tags.append("Flutter")
        elif "react" in s or "frontend" in s or "typescript" in s:
            skill_tags.append("Frontend")
        elif "backend" in s or "python" in s or "fastapi" in s:
            skill_tags.append("Backend")
        elif "sql" in s or "database" in s or "postgres" in s:
            skill_tags.append("Database")
        elif "testing" in s or "qa" in s or "pytest" in s:
            skill_tags.append("QA")
        elif "docker" in s or "devops" in s or "ci" in s:
            skill_tags.append("DevOps")
        elif "data" in s or "ml" in s:
            skill_tags.append("Data")

    spec = " ".join(dict.fromkeys(skill_tags))[:3] if skill_tags else "General"
    name = f"{target_dept}-{spec.lower().replace(' ', '-')}-specialist"

    emojis = {"development": "💻", "qa": "🧪", "design": "🎨", "devops": "⚙️",
              "data": "📊", "security": "🛡️", "docs": "📖", "hr": "👥",
              "legal": "⚖️", "marketing": "📣", "product": "🏭",
              "architecture": "🏗️", "rd": "🔬"}
    emoji = emojis.get(target_dept, "👤")

    role = f"{spec} Specialist"

    return {
        "name": name,
        "role": role,
        "emoji": emoji,
        "department": target_dept.capitalize(),
        "skills": skills,
        "description": f"{spec}-разработчик со скилами: {', '.join(skills)}",
        "reasons": hire_info["reasons"],
    }


def create_agent(suggestion: dict) -> dict:
    """Создаёт нового сотрудника (.agent.md файл).

    Args:
        suggestion: результат suggest_new_agent()

    Returns:
        dict с результатом
    """
    if "error" in suggestion:
        return suggestion

    name = suggestion["name"]
    role = suggestion["role"]
    emoji = suggestion["emoji"]
    dept = suggestion["department"]
    skills = suggestion["skills"]
    description = suggestion["description"]

    # Форматируем скилы
    skills_text = "\n".join(f"- `{s}` — {s.replace('_', ' ').title()}" for s in skills)

    # Обязанности
    responsibilities = "\n".join(
        f"{i}. Разрабатывай в рамках компетенции: {', '.join(skills[:3])}"
        for i in range(1, 2)
    )

    # Выходные артефакты
    outputs = "\n".join([
        "- `src/` — код",
        "- `tests/` — тесты",
        "- `docs/` — документация",
    ])

    # Генерируем содержимое
    content = AGENT_TEMPLATE.format(
        role=role,
        description=description,
        emoji=emoji,
        department=dept,
        skills=skills_text,
        responsibilities=responsibilities,
        outputs=outputs,
    )

    # Сохраняем файл
    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    if agent_file.exists():
        return {"error": f"Сотрудник '{name}' уже существует: {agent_file}"}

    agent_file.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "name": name,
        "file": str(agent_file.relative_to(REPO_DIR)),
        "skills": skills,
        "department": dept,
        "reasons": suggestion.get("reasons", []),
    }


def rebalance_skills(dry_run: bool = False) -> dict:
    """Перебалансирует скилы: отбирает лишнее у перегруженных.

    Args:
        dry_run: если True — не применять изменения, только показать

    Returns:
        dict с результатом
    """
    from departments.hr.skill_balance import analyze_balance

    reports = analyze_balance()
    changes = []

    for report in reports:
        for m in report.overloaded:
            excess = m.skill_count - 5  # оставляем 5 скилов
            if excess <= 0:
                continue

            to_remove = m.skills[-excess:]  # последние N скилов
            changes.append({
                "member": m.name,
                "department": report.department,
                "remove": to_remove,
                "keep_count": m.skill_count - len(to_remove),
            })

            if not dry_run:
                # Читаем файл сотрудника
                agent_file = MEMBERS_DIR / f"{m.name}.agent.md"
                if agent_file.exists():
                    content = agent_file.read_text(encoding="utf-8")
                    # Удаляем строки с这些 скилами
                    for s in to_remove:
                        content = re.sub(
                            rf'^\s*-\s*`{re.escape(s)}`.*\n?',
                            '',
                            content,
                            flags=re.MULTILINE,
                        )
                    # Чистим пустые строки
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    agent_file.write_text(content, encoding="utf-8")

    return {
        "dry_run": dry_run,
        "changes": changes,
        "total_rebalanced": len(changes),
    }


# CLI
def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "suggest"

    if cmd == "suggest":
        print(f"\n{HR_EMOJI} HR — Анализ потребности в новом сотруднике\n")
        hire = analyze_hiring_need()

        if not hire["need_hire"]:
            print("  ✅ Новый сотрудник не требуется — баланс в норме\n")
            return

        print(f"  ⚠️  Требуется новый сотрудник!\n")
        for r in hire["reasons"]:
            print(f"     • {r}")
        print()

        suggestion = suggest_new_agent()
        if "error" in suggestion:
            print(f"  {suggestion['error']}\n")
            return

        print(f"  Предлагаемый сотрудник:\n")
        print(f"     {suggestion['emoji']} {suggestion['role']}")
        print(f"     Отдел: {suggestion['department']}")
        print(f"     Скилы: {', '.join(suggestion['skills'])}")
        print(f"     Файл: .github/agents/members/{suggestion['name']}.agent.md")
        print()
        print(f"  💡 python team.py hr hire — создать сотрудника")
        print()

    elif cmd == "hire":
        suggestion = suggest_new_agent()
        result = create_agent(suggestion)
        if "error" in result:
            print(f"  ❌ {result['error']}")
        else:
            print(f"\n{HR_EMOJI} HR — Создан новый сотрудник\n")
            print(f"  ✅ {result['name']}")
            print(f"  📄 Файл: {result['file']}")
            print(f"  💡 Скилы: {', '.join(result['skills'])}")
            print(f"  🏢 Отдел: {result['department']}")
            if result.get("reasons"):
                print(f"\n  Причины найма:")
                for r in result["reasons"]:
                    print(f"     • {r}")
        print()

    elif cmd == "rebalance":
        dry = "--dry-run" in sys.argv
        if dry:
            print(f"\n{HR_EMOJI} HR — Пробный перебаланс скилов (dry-run)\n")
        else:
            print(f"\n{HR_EMOJI} HR — Перебаланс скилов\n")

        result = rebalance_skills(dry_run=dry)
        if not result["changes"]:
            print("  ✅ Перегруженных сотрудников нет\n")
            return

        for c in result["changes"]:
            print(f"  🔄 {c['member']} ({c['department']}): "
                  f"удалено {len(c['remove'])} скилов, "
                  f"осталось {c['keep_count']}")
            print(f"     Убрано: {', '.join(c['remove'])}")

        print(f"\n  Всего затронуто: {result['total_rebalanced']} сотрудников")
        if dry:
            print(f"  🔍 Это dry-run — изменения не применены")
            print(f"  💡 python team.py hr rebalance — применить")
        print()


if __name__ == "__main__":
    _cli()
