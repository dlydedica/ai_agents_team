#!/usr/bin/env python3
"""
👥 HR — Анализатор баланса скилов сотрудников.

Следит, чтобы:
  - У каждого сотрудника было достаточно скилов (не менее 2)
  - Скилы не дублировались между сотрудниками без необходимости
  - Не было перегруженности (более 6 скилов на одного сотрудника)
  - Отдел имел равномерное покрытие
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

REPO_DIR = Path(__file__).resolve().parent.parent.parent
MEMBERS_DIR = REPO_DIR / ".github" / "agents" / "members"
DEPARTMENTS_DIR = REPO_DIR / ".github" / "agents" / "departments"
SKILLS_DIR = REPO_DIR / "skills"

# Оптимальный диапазон скилов на сотрудника
MIN_SKILLS = 2
MAX_SKILLS = 6
OPTIMAL_SKILLS = (3, 5)


@dataclass
class MemberSkills:
    """Скилы одного сотрудника."""
    name: str
    role: str
    department: str
    skills: list[str]
    skill_count: int


@dataclass
class BalanceReport:
    """Отчёт о балансе скилов."""
    department: str
    members: list[MemberSkills]
    overloaded: list[MemberSkills]  # больше MAX_SKILLS
    underloaded: list[MemberSkills]  # меньше MIN_SKILLS
    optimal: list[MemberSkills]  # в OPTIMAL_SKILLS
    duplicates: list[tuple[str, str, str]]  # (skill, member1, member2)
    gaps: list[str]  # технологии без сотрудников
    score: int  # 0-100


def _parse_agent_skills(filepath: Path) -> tuple[str, str, list[str]]:
    """Извлекает роль, отдел и список скилов из .agent.md файла."""
    role = filepath.stem
    department = "unknown"
    skills = []

    try:
        content = filepath.read_text(encoding="utf-8")
        in_skills_section = False
        for line in content.split("\n"):
            stripped = line.strip()

            # Извлекаем роль из заголовка
            if stripped.startswith("# ") and not role:
                role = stripped.strip("# ").strip()

            # Ищем секцию "## Скилы"
            if stripped.startswith("## Скилы"):
                in_skills_section = True
                continue

            # Если началась другая секция — выходим из скилов
            if in_skills_section and stripped.startswith("## "):
                in_skills_section = False
                continue

            # Извлекаем скилы внутри секции: - `skill_name` — описание
            if in_skills_section:
                match = re.match(r'^\s*-\s*`(.+?)`', stripped)
                if match:
                    skills.append(match.group(1))
    except Exception:
        pass

    return role, department, skills


def _get_department_for_member(member_name: str) -> str:
    """Определяет отдел сотрудника по agent-файлу (department: в frontmatter)."""
    clean_name = member_name.replace(".agent", "")
    agent_file = MEMBERS_DIR / f"{clean_name}.agent.md"
    if not agent_file.exists():
        return "unknown"
    try:
        content = agent_file.read_text(encoding="utf-8")
        in_frontmatter = False
        for line in content.split("\n"):
            stripped = line.strip()
            # Отслеживаем YAML frontmatter
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if not in_frontmatter:
                continue

            # Поле department: в frontmatter
            if stripped.startswith("department:"):
                dept = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if dept:
                    return dept.lower()

        # Fallback: ищем в description (для старых файлов без department:)
        for line in content.split("\n"):
            if line.strip().startswith("description:"):
                desc = line.strip()
                for dept in ["development", "design", "qa", "devops", "data",
                              "security", "docs", "hr", "legal", "marketing",
                              "product", "architecture", "rd"]:
                    if dept in desc.lower():
                        return dept
                dev_keywords = ["flutter", "dart", "react", "python", "backend",
                                "frontend", "fullstack", "stac", "typescript",
                                "developer", "full-stack", "web"]
                if any(kw in desc.lower() for kw in dev_keywords):
                    return "development"
    except Exception:
        pass
    return "unknown"


def analyze_balance() -> list[BalanceReport]:
    """Анализирует баланс скилов всех сотрудников по отделам.

    Returns:
        Список отчётов BalanceReport по каждому отделу
    """
    if not MEMBERS_DIR.exists():
        return []

    # Собираем всех сотрудников
    all_members = []
    for f in sorted(MEMBERS_DIR.glob("*.agent.md")):
        role, _, skills = _parse_agent_skills(f)
        name = f.stem.replace(".agent", "")
        dept = _get_department_for_member(name)
        all_members.append(MemberSkills(
            name=name,
            role=role,
            department=dept,
            skills=skills,
            skill_count=len(skills),
        ))

    # Группируем по отделам
    departments = {}
    for m in all_members:
        departments.setdefault(m.department, []).append(m)

    reports = []
    for dept, members in sorted(departments.items()):
        overloaded = [m for m in members if m.skill_count > MAX_SKILLS]
        underloaded = [m for m in members if m.skill_count < MIN_SKILLS]
        optimal = [m for m in members if OPTIMAL_SKILLS[0] <= m.skill_count <= OPTIMAL_SKILLS[1]]

        # Поиск дубликатов скилов между сотрудниками
        duplicates = []
        all_skill_pairs = []
        for m in members:
            for s in m.skills:
                all_skill_pairs.append((s, m.name))

        for i, (skill, m1) in enumerate(all_skill_pairs):
            for skill2, m2 in all_skill_pairs[i + 1:]:
                if skill == skill2 and m1 != m2:
                    dup = (skill, m1, m2)
                    if dup not in duplicates and (skill, m2, m1) not in duplicates:
                        duplicates.append(dup)

        # Поиск пробелов: скилы, которые есть в реестре, но нет ни у одного сотрудника
        gaps = _find_skill_gaps(members)

        # Оценка (0-100)
        score = _calculate_score(members, overloaded, underloaded, duplicates, gaps)

        reports.append(BalanceReport(
            department=dept,
            members=members,
            overloaded=overloaded,
            underloaded=underloaded,
            optimal=optimal,
            duplicates=duplicates,
            gaps=gaps,
            score=score,
        ))

    return reports


def _find_skill_gaps(members: list[MemberSkills]) -> list[str]:
    """Находит технологии из реестра, которые не покрыты сотрудниками."""
    try:
        sys.path.insert(0, str(SKILLS_DIR.parent))
        from skills.registry import discover_skills
        all_skills = discover_skills()
    except Exception:
        return []

    member_skill_names = set()
    for m in members:
        for s in m.skills:
            member_skill_names.add(s)

    gaps = []
    for s in all_skills:
        name = s["frontmatter"].get("name", "")
        if name and name not in member_skill_names:
            gaps.append(name)

    return gaps[:10]  # не больше 10


def _calculate_score(
    members: list[MemberSkills],
    overloaded: list[MemberSkills],
    underloaded: list[MemberSkills],
    duplicates: list[tuple],
    gaps: list[str],
) -> int:
    """Вычисляет оценку баланса отдела (0-100)."""
    if not members:
        return 0

    score = 100

    # Штраф за перегруженных
    score -= len(overloaded) * 15

    # Штраф за недогруженных
    score -= len(underloaded) * 20

    # Штраф за дубликаты (но дублирование OK если скил ключевой)
    score -= len(duplicates) * 5

    # Штраф за пробелы
    score -= len(gaps) * 3

    # Бонус за оптимальных
    optimal_ratio = len([m for m in members if OPTIMAL_SKILLS[0] <= m.skill_count <= OPTIMAL_SKILLS[1]]) / len(members)
    score += int(optimal_ratio * 10)

    return max(0, min(100, score))


def print_report(reports: list[BalanceReport]):
    """Выводит отчёт о балансе скилов."""
    print("\n" + "=" * 60)
    print("  👥 HR — Анализ баланса скилов сотрудников")
    print("=" * 60)

    # Сводка
    total_members = sum(len(r.members) for r in reports)
    total_overloaded = sum(len(r.overloaded) for r in reports)
    total_underloaded = sum(len(r.underloaded) for r in reports)
    total_duplicates = sum(len(r.duplicates) for r in reports)

    print(f"\n  📊 Сводка: {total_members} сотрудников, {len(reports)} отделов\n")

    if total_overloaded:
        print(f"  ⚠️  Перегружены скилами (>6): {total_overloaded} сотрудников")
    if total_underloaded:
        print(f"  ⚠️  Недогружены скилами (<2): {total_underloaded} сотрудников")
    if total_duplicates:
        print(f"  🔄 Дублирующихся скилов: {total_duplicates}")
    print()

    # По отделам
    for report in reports:
        emoji = {
            "development": "💻", "design": "🎨", "qa": "🧪", "devops": "⚙️",
            "data": "📊", "security": "🛡️", "docs": "📖", "hr": "👥",
            "legal": "⚖️", "marketing": "📣", "product": "🏭",
            "architecture": "🏗️", "rd": "🔬",
        }.get(report.department, "📁")

        # Цветовая индикация
        if report.score >= 80:
            status = "✅"
        elif report.score >= 50:
            status = "⚠️"
        else:
            status = "❌"

        print(f"  {emoji} {report.department.capitalize():15s} {status} Оценка: {report.score}/100")

        for m in report.members:
            bar = "█" * min(m.skill_count, MAX_SKILLS) + "░" * max(0, MAX_SKILLS - m.skill_count)
            warn = ""
            if m.skill_count > MAX_SKILLS:
                warn = " ⚠️  перегруз"
            elif m.skill_count < MIN_SKILLS:
                warn = " ⚠️  недостаточно"
            print(f"     👤 {m.name:30s} |{bar}| {m.skill_count} скилов{warn}")

        if report.duplicates:
            print(f"     🔄 Дубликаты:")
            for skill, m1, m2 in report.duplicates[:3]:
                print(f"        • `{skill}` — {m1} + {m2}")

        if report.gaps:
            print(f"     📋 Скилы без сотрудника: {', '.join(report.gaps[:5])}")

        print()

    # Рекомендации
    print("  💡 Рекомендации HR:\n")

    if total_overloaded:
        print(f"     • Перегруженным сотрудникам: распределить часть скилов")
    if total_underloaded:
        print(f"     • Недогруженным сотрудникам: добавить скилы из gaps")
    if total_duplicates > len(reports) * 2:
        print(f"     • Много дубликатов — возможно, стоит создать узких специалистов")
    if all(r.score >= 80 for r in reports):
        print(f"     ✅ Отличный баланс! Команда сбалансирована.")
    print()


def _cli():
    """CLI для skill_balance.py."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "balance"

    if cmd == "balance":
        reports = analyze_balance()
        print_report(reports)
    elif cmd == "members":
        # Показать детально всех сотрудников со скилами
        reports = analyze_balance()
        for r in reports:
            for m in r.members:
                print(f"{m.name:30s} | {m.role:40s} | {m.skill_count} скилов: {', '.join(m.skills[:5])}")


if __name__ == "__main__":
    _cli()
