"""
Назначение скилов членам команды AI DevCorp.

Позволяет:
  - Назначать скилы отделам (по технологиям)
  - Показывать, какие скилы доступны для отдела
  - Автоматически рекомендовать скилы под проект
  - Генерировать отчёт о покрытии отдела скилами
"""

import re
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from skills.registry import discover_skills, search_skills

SKILLS_DIR = Path(__file__).parent
DEPARTMENTS_DIR = SKILLS_DIR.parent / "departments"

DEPARTMENT_EMOJI = {
    "product": "🏭",
    "architecture": "🏗️",
    "development": "💻",
    "qa": "🧪",
    "devops": "⚙️",
    "design": "🎨",
    "docs": "📖",
    "hr": "👥",
    "security": "🛡️",
    "data": "📊",
    "rd": "🔬",
    "legal": "⚖️",
    "marketing": "📣",
}

# Маппинг: отдел → ключевые технологии для рекомендации скилов
DEPARTMENT_TECH_MAP = {
    "development": [
        "python", "javascript", "typescript", "dart", "flutter", "go", "rust",
        "java", "kotlin", "swift", "react", "vue", "angular", "nodejs",
        "fastapi", "django", "spring", "backend", "frontend", "fullstack",
        "api", "graphql", "rest", "microservices",
    ],
    "qa": [
        "testing", "pytest", "selenium", "cypress", "playwright",
        "unit-test", "integration-test", "e2e", "quality-assurance",
    ],
    "devops": [
        "docker", "kubernetes", "ci/cd", "terraform", "ansible",
        "aws", "gcp", "azure", "linux", "monitoring", "observability",
    ],
    "design": [
        "figma", "ui", "ux", "design-system", "prototyping",
        "accessibility", "material-design", "sdui",
    ],
    "data": [
        "sql", "postgresql", "mysql", "mongodb", "redis", "etl",
        "data-engineering", "data-science", "ml", "machine-learning",
        "airflow", "spark", "dbt", "analytics",
    ],
    "security": [
        "security", "pentest", "owasp", "audit", "vulnerability",
        "compliance", "authentication", "authorization",
    ],
    "architecture": [
        "architecture", "microservices", "system-design", "ddd",
        "event-driven", "scalability", "patterns", "solid",
    ],
    "product": [
        "product-management", "requirements", "analysis", "specification",
        "user-stories", "roadmap", "backlog",
    ],
    "docs": [
        "documentation", "technical-writing", "api-docs", "readme",
        "markdown", "wiki",
    ],
    "hr": [
        "hr", "performance-review", "recruitment", "onboarding",
        "team-building", "retrospective",
    ],
    "rd": [
        "research", "prototyping", "poc", "innovation", "benchmarking",
        "experiment",
    ],
    "legal": [
        "legal", "license", "oss", "ip", "compliance", "contract",
    ],
    "marketing": [
        "marketing", "content", "seo", "social-media", "branding",
        "analytics", "growth",
    ],
}


@dataclass
class DepartmentSkillCoverage:
    """Покрытие отдела скилами."""
    department: str
    total_skills: int
    builtin_skills: int
    external_skills: int
    skills: list[dict]
    missing_tags: list[str]


def assign_skill_to_department(skill_name: str, department: str) -> dict:
    """Назначает скил отделу (обновляет метаданные скила).

    Args:
        skill_name: Имя скила
        department: Имя отдела

    Returns:
        Результат операции
    """
    skill = None
    all_skills = discover_skills()

    for s in all_skills:
        if s["frontmatter"].get("name") == skill_name:
            skill = s
            break

    if not skill:
        return {"error": f"Скил '{skill_name}' не найден"}

    # Проверяем, что отдел существует
    valid_depts = {
        "product", "architecture", "development", "qa", "devops",
        "design", "docs", "hr", "security", "data", "rd", "legal", "marketing",
    }
    if department not in valid_depts:
        return {"error": f"Неизвестный отдел '{department}'"}

    meta = skill["frontmatter"]
    current_depts = meta.get("departments", [])
    if isinstance(current_depts, str):
        current_depts = [current_depts]

    if department in current_depts:
        return {"warning": f"Скил '{skill_name}' уже назначен отделу '{department}'", "skill": skill}

    # Обновляем departments в frontmatter
    current_depts.append(department)
    meta["departments"] = current_depts

    # Сохраняем изменения в файл (если это builtin-скил)
    skill_file = SKILLS_DIR / skill.get("filepath", "")
    if skill_file.exists():
        content = skill_file.read_text(encoding="utf-8")
        # Обновляем строку departments в YAML
        dept_str = ", ".join(current_depts)
        content = re.sub(
            r"^departments:.*$",
            f"departments: [{dept_str}]",
            content,
            flags=re.MULTILINE,
        )
        skill_file.write_text(content, encoding="utf-8")
        return {"success": True, "message": f"Скил '{skill_name}' назначен отделу '{department}'"}
    else:
        return {"error": f"Файл скила не найден: {skill_file}"}


def analyze_department_coverage(department: str) -> DepartmentSkillCoverage:
    """Анализирует покрытие отдела скилами.

    Args:
        department: Имя отдела

    Returns:
        Объект DepartmentSkillCoverage с анализом
    """
    skills = search_skills(department=department, skill_type="all")

    builtin = [s for s in skills if s.get("skill_type") == "builtin"]
    external = [s for s in skills if s.get("skill_type") == "external"]

    # Какие технологии НЕ покрыты скилами
    all_tags = set()
    for s in skills:
        tags = s["frontmatter"].get("tags", [])
        if isinstance(tags, list):
            all_tags.update(t.lower() for t in tags)

    expected_tags = DEPARTMENT_TECH_MAP.get(department, [])
    missing = [t for t in expected_tags if t not in all_tags]

    return DepartmentSkillCoverage(
        department=department,
        total_skills=len(skills),
        builtin_skills=len(builtin),
        external_skills=len(external),
        skills=skills,
        missing_tags=missing,
    )


def suggest_skills_for_department(department: str) -> list[dict]:
    """Предлагает скилы, которые стоит добавить отделу.

    Анализирует недостающие технологии и ищет подходящие скилы.
    """
    coverage = analyze_department_coverage(department)
    suggestions = []

    # Ищем скилы по недостающим технологиям
    for tech in coverage.missing_tags:
        found = search_skills(tags=[tech], skill_type="all")
        for s in found:
            # Проверяем, что скил ещё не назначен этому отделу
            depts = s["frontmatter"].get("departments", [])
            if isinstance(depts, list) and department not in depts:
                suggestions.append({
                    "skill": s,
                    "reason": f"Покрывает технологию: {tech}",
                    "action": f"Назначить: python team.py skills assign {s['frontmatter']['name']} {department}",
                })

    return suggestions


def generate_coverage_report() -> list[DepartmentSkillCoverage]:
    """Генерирует отчёт о покрытии скилами всех отделов."""
    from team import DEPARTMENT_EMOJI as TEAM_EMOJI

    reports = []
    for dept in sorted(DEPARTMENT_TECH_MAP.keys()):
        report = analyze_department_coverage(dept)
        reports.append(report)

    return reports


def _cli():
    """CLI для assigner.py."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"

    if cmd == "report":
        print("\n📊 Отчёт о покрытии отделов скилами:\n")
        emoji_map = DEPARTMENT_EMOJI
        for dept in sorted(DEPARTMENT_TECH_MAP.keys()):
            cov = analyze_department_coverage(dept)
            emoji = emoji_map.get(dept, "📁")
            bar = "█" * min(cov.total_skills, 20) + "░" * max(0, 20 - min(cov.total_skills, 20))
            print(f"  {emoji} {dept.capitalize():15s} |{bar}| {cov.total_skills:2d} скилов "
                  f"({cov.builtin_skills} builtin + {cov.external_skills} external)")

            if cov.missing_tags:
                print(f"       ⚠️  Непокрытые технологии: {', '.join(cov.missing_tags[:5])}")
            print()

    elif cmd == "analyze":
        dept = sys.argv[2] if len(sys.argv) > 2 else ""
        if not dept:
            print("❌ Укажите отдел: python skills/assigner.py analyze <department>")
            sys.exit(1)

        cov = analyze_department_coverage(dept)
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        print(f"\n{emoji} Анализ отдела {dept.capitalize()}:\n")
        print(f"  Всего скилов: {cov.total_skills}")
        print(f"  Builtin: {cov.builtin_skills}")
        print(f"  External: {cov.external_skills}")
        print()
        for s in cov.skills:
            meta = s["frontmatter"]
            icon = "📦" if s.get("skill_type") == "builtin" else "🌐"
            grade = meta.get("grade", "?")
            print(f"  {icon} [{grade}] {meta.get('name', '?')} — {meta.get('description', '')[:100]}")
        print()
        if cov.missing_tags:
            print(f"  ⚠️  Непокрытые технологии: {', '.join(cov.missing_tags)}")
            suggestions = suggest_skills_for_department(dept)
            if suggestions:
                print(f"\n  💡 Рекомендации:")
                for s in suggestions[:5]:
                    print(f"     • {s['skill']['frontmatter']['name']} — {s['reason']}")

    elif cmd == "assign":
        skill_name = sys.argv[2] if len(sys.argv) > 2 else ""
        dept = sys.argv[3] if len(sys.argv) > 3 else ""
        if not skill_name or not dept:
            print("❌ Использование: python skills/assigner.py assign <skill_name> <department>")
            sys.exit(1)

        result = assign_skill_to_department(skill_name, dept)
        if "error" in result:
            print(f"❌ {result['error']}")
        elif "warning" in result:
            print(f"⚠️  {result['warning']}")
        else:
            print(f"✅ {result['message']}")


if __name__ == "__main__":
    _cli()
