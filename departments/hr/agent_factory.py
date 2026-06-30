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

# ── Grade-Based Permission System (ADR-003) ───────────────────────────────
GRADE_TOOLS: dict[str, list[str]] = {
    "J": ["read", "search", "edit"],
    "M": ["read", "search", "edit", "execute"],
    "S": ["read", "search", "edit", "execute"],
    "L": ["read", "search", "edit", "execute", "web"],
}

# Исключения по типу роли
ROLE_EXCEPTIONS: dict[str, callable] = {
    "read_only": lambda _: ["read", "search"],                    # compliance
    "manual": lambda t: [x for x in t if x != "execute"],         # manual tester
    "research": lambda t: list(set(t) | {"web"}),                  # rd, talent scout
    "market": lambda t: list(set(t) | {"web"}),                    # product, marketing
}

# Роли-исключения определяются по role_key
READ_ONLY_KEYS = {"compliance", "compliance_officer"}
RESEARCH_KEYS = {"rd", "research", "talent_scout", "innovation", "research_engineer"}
MANUAL_KEYS = {"manual", "manual_tester", "tester"}
MARKET_KEYS = {"product", "marketing", "content", "growth", "brand", "market"}


def _resolve_tools(grade: str, role_key: str) -> list[str]:
    """Определить tools для сотрудника по грейду и роли."""
    grade = grade.upper()
    base = list(GRADE_TOOLS.get(grade, GRADE_TOOLS["M"]))

    # Read-only — самый высокий приоритет
    if any(k in role_key for k in READ_ONLY_KEYS):
        return ROLE_EXCEPTIONS["read_only"](base)

    manual = any(k in role_key for k in MANUAL_KEYS)
    research = any(k in role_key for k in RESEARCH_KEYS)
    market = any(k in role_key for k in MARKET_KEYS)

    tools = set(base)
    if manual:
        tools.discard("execute")
    if research:
        tools.add("web")
    if market:
        tools.add("web")

    return sorted(tools)


AGENT_TEMPLATE = """---
alias: "{role}"
grade: "M"
department: "{dept}"
tools: [read, search, edit, execute]
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

    # Фильтруем candidates: оставляем только скилы, релевантные отделу
    dept_tech_map = {
        "development": ["flutter", "dart", "python", "react", "typescript",
                        "backend", "frontend", "fullstack", "stac", "sdui",
                        "fastapi", "sqlalchemy", "postgresql", "redis", "nodejs",
                        "docker", "testing", "pytest", "ci", "alembic", "pydantic"],
        "qa": ["testing", "pytest", "qa", "selenium", "automation"],
        "devops": ["docker", "devops", "ci", "kubernetes", "terraform"],
        "design": ["design", "ui", "ux", "figma", "sdui"],
        "data": ["data", "sql", "ml", "etl", "analytics"],
        "marketing": ["marketing", "content", "seo", "social"],
        "security": ["security", "pentest", "audit"],
        "docs": ["docs", "documentation"],
        "hr": ["hr", "performance"],
        "legal": ["legal", "license", "oss"],
        "product": ["product", "management"],
        "architecture": ["architecture", "microservices", "system"],
        "rd": ["research", "prototyping", "rd"],
    }

    # Определяем целевой отдел (где больше всего проблем)
    dept_counts = {}
    for o in overloaded:
        dept_counts[o["department"]] = dept_counts.get(o["department"], 0) + 1
    target_dept = max(dept_counts, key=dept_counts.get) if dept_counts else "development"

    # Фильтруем candidates по технологиям целевого отдела
    relevant_techs = dept_tech_map.get(target_dept, [])
    filtered = [c for c in candidates
                if any(t in c.lower() for t in relevant_techs)]

    # Проверка: если уже нанимали недавно — не предлагаем снова
    cooldown_file = Path(__file__).parent / "last_hire.txt"
    if cooldown_file.exists():
        from datetime import datetime
        try:
            last_hire = cooldown_file.read_text(encoding="utf-8").strip()
            if last_hire:
                last_time = datetime.fromisoformat(last_hire)
                delta = datetime.now() - last_time
                if delta.total_seconds() < 300:  # 5 минут cooldown
                    reasons.append("Недавно уже нанимали — подождите 5 минут")
                    need_hire = False
        except Exception:
            pass

    return {
        "need_hire": need_hire,
        "reasons": reasons,
        "overloaded": overloaded,
        "target_department": target_dept,
        "candidates": sorted(filtered) if filtered else sorted(candidates)[:5],
    }


def _write_hire_cooldown():
    """Записывает время найма для cooldown."""
    cooldown_file = Path(__file__).parent / "last_hire.txt"
    from datetime import datetime
    cooldown_file.write_text(datetime.now().isoformat(), encoding="utf-8")


def suggest_new_agent() -> dict:
    """Предлагает параметры для нового сотрудника.

    Returns:
        dict: name, role, emoji, department, skills, description
    """
    hire_info = analyze_hiring_need()

    if not hire_info["need_hire"]:
        return {"error": "Новый сотрудник не требуется — баланс в норме"}

    # Определяем отдел для нового сотрудника (из отфильтрованных данных)
    target_dept = hire_info.get("target_department", "development")

    # Определяем специализацию — ПРЕДПОЧИТАЕМ gaps (непокрытые скилы)
    # а не дубликаты (чтобы не создавать ещё больше дубликатов)
    from departments.hr.skill_balance import analyze_balance
    reports = analyze_balance()
    for report in reports:
        if report.department == target_dept and report.gaps:
            # Отдаём предпочтение gaps
            gap_candidates = [g for g in report.gaps
                              if any(t in g.lower() for t in
                                     ["flutter", "dart", "python", "react", "backend",
                                      "frontend", "fullstack", "stac", "sql", "database",
                                      "testing", "docker", "devops", "data", "ml",
                                      "security", "node", "redis"])]
            if gap_candidates:
                # Смешиваем: gaps + немного из candidates
                hire_info["candidates"] = gap_candidates[:4] + hire_info["candidates"][:2]
            break

    candidates = hire_info["candidates"]
    if not candidates:
        candidates = ["general"]

    # Определяем навыки (берём уникальные, макс 5)
    skills = list(dict.fromkeys(candidates))[:5]

    # Генерируем имя и роль
    spec_map = {
        "flutter": "Flutter", "dart": "Flutter",
        "react": "Frontend", "frontend": "Frontend", "typescript": "Frontend", "ui": "Frontend",
        "backend": "Backend", "python": "Backend", "fastapi": "Backend",
        "fullstack": "Fullstack",
        "sql": "DB", "database": "DB", "postgres": "DB", "mysql": "DB",
        "testing": "QA", "qa": "QA", "pytest": "QA",
        "docker": "DevOps", "devops": "DevOps", "kubernetes": "DevOps",
        "data": "Data", "ml": "Data", "etl": "Data",
        "security": "Security", "pentest": "Security",
        "marketing": "Marketing", "content": "Marketing",
        "stac": "Stac", "sdui": "Stac",
        "nodejs": "NodeJS", "redis": "Redis",
    }

    seen = []
    for s in skills:
        for key, label in spec_map.items():
            if key in s.lower() and label not in seen:
                seen.append(label)
                break
    spec = " + ".join(seen[:3]) if seen else "General"
    name = f"{target_dept}-{spec.lower().replace(' + ', '-')[:25]}-specialist"

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


def create_agent(suggestion: dict, grade: str = "M") -> dict:
    """Создаёт нового сотрудника (.agent.md файл) с валидацией permissions.

    Args:
        suggestion: результат suggest_new_agent()
        grade: грейд сотрудника (J/M/S/L) — по умолчанию Middle

    Returns:
        dict с результатом
    """
    if "error" in suggestion:
        return suggestion

    if grade.upper() not in ("J", "M", "S", "L"):
        return {"error": f"Некорректный грейд: {grade}. Допустимые: J, M, S, L"}

    name = suggestion["name"]
    role = suggestion["role"]
    emoji = suggestion["emoji"]
    dept = suggestion["department"]
    skills = suggestion["skills"]
    description = suggestion["description"]

    # Определяем tools по грейду и роли
    grade_key = grade.upper()
    role_key = name.split("-")[0].lower()  # извлекаем ключ роли из имени
    tools = _resolve_tools(grade_key, role_key)

    # Если имя занято — добавляем счётчик
    counter = 1
    base_name = name
    while (MEMBERS_DIR / f"{name}.agent.md").exists():
        counter += 1
        name = f"{base_name}-v{counter}"

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

    # Сериализуем tools для YAML
    tools_yaml = ", ".join(tools)

    # Генерируем содержимое
    content = AGENT_TEMPLATE.format(
        role=role,
        dept=dept.lower(),
        emoji=emoji,
        department=dept,
        skills=skills_text,
        responsibilities=responsibilities,
        outputs=outputs,
    )

    # Подменяем tools в frontmatter на корректные для грейда
    content = content.replace(
        "tools: [read, search, edit, execute]",
        f"tools: [{tools_yaml}]"
    )
    # Подменяем grade
    content = content.replace(
        'grade: "M"',
        f'grade: "{grade_key}"'
    )

    # Сохраняем файл
    agent_file = MEMBERS_DIR / f"{name}.agent.md"
    agent_file.write_text(content, encoding="utf-8")

    # Записываем cooldown
    _write_hire_cooldown()

    return {
        "success": True,
        "name": name,
        "file": str(agent_file.relative_to(REPO_DIR)),
        "skills": skills,
        "department": dept,
        "grade": grade_key,
        "tools": tools,
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

    def _change_entry(member, report, to_remove):
        return {
            "member": member.name,
            "department": report.department,
            "remove": to_remove,
            "keep_count": member.skill_count - len(to_remove),
        }

    for report in reports:
        # Удаляем дубликаты у клонов (-v2, -v3)
        for m in report.members:
            if "-v" not in m.name:
                continue
            # Оставляем только 2 уникальных скила клонам
            excess = max(0, m.skill_count - 2)
            if excess <= 0:
                continue
            to_remove = m.skills[-excess:]
            changes.append(_change_entry(m, report, to_remove))
            if not dry_run:
                agent_file = MEMBERS_DIR / f"{m.name}.agent.md"
                if agent_file.exists():
                    content = agent_file.read_text(encoding="utf-8")
                    for s in to_remove:
                        content = re.sub(
                            rf'^\s*-\s*`{re.escape(s)}`.*\n?',
                            '', content, flags=re.MULTILINE,
                        )
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    agent_file.write_text(content, encoding="utf-8")

        for m in report.overloaded:
            excess = m.skill_count - 5  # оставляем 5 скилов
            if excess <= 0:
                continue

            to_remove = m.skills[-excess:]  # последние N скилов
            changes.append(_change_entry(m, report, to_remove))

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


def overhaul(dry_run: bool = False) -> dict:
    """Полный пересмотр команды: баланс → найм → увольнение → отчёт.

    Автоматически:
    1. Перебалансирует скилы (rebalance)
    2. Увольняет клонов (-v2, -v3...)
    3. Нанимает нового сотрудника если gaps > 5
    4. Даёт отчёт о здоровье команды

    Args:
        dry_run: если True — только показать, не применять

    Returns:
        dict с результатом
    """
    from departments.hr.lifecycle import archive_member, demote_member, set_rating
    from departments.hr.skill_balance import analyze_balance

    log = []
    changes = {"hired": 0, "fired": 0, "rebalanced": 0}

    print(f"\n{'='*60}")
    print(f"  👥 HR — Полный пересмотр команды {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}\n")

    # Шаг 1: Анализ текущего состояния
    reports = analyze_balance()
    total = sum(len(r.members) for r in reports)
    print(f"  📊 Текущий состав: {total} сотрудников\n")

    for report in reports:
        emoji = {"development": "💻", "qa": "🧪"}.get(report.department, "📁")
        status = "✅" if report.score >= 50 else "❌"
        print(f"  {emoji} {report.department.capitalize():15s} {status} Оценка: {report.score}/100")

        # Шаг 2: Увольняем клонов (-v2, -v3...)
        clones = [m for m in report.members if "-v" in m.name]
        clones_to_fire = clones[1:]  # оставляем одного, остальных увольняем
        if clones_to_fire:
            for clone in clones_to_fire:
                print(f"     🗄️  Увольнение клона: {clone.name}")
                if not dry_run:
                    archive_member(clone.name, "Клон, заменён основным")
                    changes["fired"] += 1

        # Шаг 3: Перебалансировка
        rb_result = rebalance_skills(dry_run=dry_run)
        changes["rebalanced"] += rb_result["total_rebalanced"]

        # Шаг 4: Найм если gaps > 5
        if len(report.gaps) >= 5:
            from departments.hr.agent_factory import analyze_hiring_need, suggest_new_agent, create_agent
            hire_info = analyze_hiring_need()
            if hire_info["need_hire"]:
                suggestion = suggest_new_agent()
                if "error" not in suggestion and not dry_run:
                    result = create_agent(suggestion)
                    if "success" in result:
                        print(f"     👤 Найм: {result['name']} ({', '.join(result['skills'][:3])}...)")
                        changes["hired"] += 1
                    else:
                        print(f"     ⚠️  Найм не удался: {result.get('error', '')}")
                elif dry_run:
                    print(f"     💡 Будет нанят: {suggestion.get('role', '?')} "
                          f"со скилами: {', '.join(suggestion.get('skills', [])[:3])}...")
                    changes["hired"] = 1
        print()

    # Итог
    print(f"  {'='*50}")
    if dry_run:
        print(f"  🔍 DRY RUN — изменения не применены")
    print(f"  📋 Результаты:")
    print(f"     👤 Нанято: {changes['hired']}")
    print(f"     🗄️  Уволено: {changes['fired']}")
    print(f"     🔄 Перебалансировано: {changes['rebalanced']}")

    if not dry_run and (changes["hired"] or changes["fired"] or changes["rebalanced"]):
        print(f"\n  ✅ Команда пересмотрена. Запустите python team.py hr balance для проверки.")

    print()

    return changes


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
