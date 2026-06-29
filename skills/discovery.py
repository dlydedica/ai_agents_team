"""
Поиск и анализ внешних скилов для AI DevCorp.

Позволяет:
  - Искать скилы на GitHub по технологии/специальности
  - Анализировать репозиторий на наличие SKILL.md / .skill.md файлов
  - Предлагать список скилов к установке
  - Определять, какому отделу подходит скил
"""

import json
import re
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

SKILLS_DIR = Path(__file__).parent
EXTERNAL_DIR = SKILLS_DIR / "external"
REGISTRY_FILE = EXTERNAL_DIR / "registry.json"
KNOWN_REPOS_FILE = SKILLS_DIR / "known_repos.json"


def _load_known_repos() -> dict:
    """Загружает базу известных репозиториев из JSON-файла."""
    try:
        if KNOWN_REPOS_FILE.exists():
            data = json.loads(KNOWN_REPOS_FILE.read_text(encoding="utf-8"))
            return data.get("repos", {})
    except (json.JSONDecodeError, OSError):
        pass
    return {}


# База известных репозиториев со скилами (загружается из known_repos.json)
KNOWN_SKILL_REPOS = _load_known_repos()

# Маппинг технологий на отделы
TECH_TO_DEPARTMENT = {
    "python": "development",
    "dart": "development",
    "flutter": "development",
    "javascript": "development",
    "typescript": "development",
    "react": "development",
    "vue": "development",
    "angular": "development",
    "nodejs": "development",
    "go": "development",
    "rust": "development",
    "java": "development",
    "kotlin": "development",
    "swift": "development",
    "sql": "data",
    "database": "data",
    "postgresql": "data",
    "mysql": "data",
    "mongodb": "data",
    "redis": "development",
    "docker": "devops",
    "kubernetes": "devops",
    "ci/cd": "devops",
    "aws": "devops",
    "gcp": "devops",
    "azure": "devops",
    "terraform": "devops",
    "figma": "design",
    "ui": "design",
    "ux": "design",
    "design-system": "design",
    "testing": "qa",
    "pytest": "qa",
    "selenium": "qa",
    "security": "security",
    "pentest": "security",
    "ml": "data",
    "machine-learning": "data",
    "data-engineering": "data",
    "data-science": "data",
    "research": "rd",
    "prototyping": "rd",
    "marketing": "marketing",
    "legal": "legal",
    "docs": "docs",
    "hr": "hr",
}


@dataclass
class SkillSuggestion:
    """Предложение скила к установке."""

    name: str
    repo: str
    url: str
    description: str
    departments: list[str]
    technologies: list[str]
    is_installed: bool = False
    skills_count: int = 0
    stars: int = 0


def search_github_skills(query: str, max_results: int = 10) -> list[dict]:
    """Ищет репозитории со скилами на GitHub по запросу.

    Использует GitHub Search API для поиска репозиториев,
    содержащих SKILL.md файлы.

    Args:
        query: Поисковый запрос (технология, специальность)
        max_results: Максимум результатов

    Returns:
        Список найденных репозиториев
    """
    results = []

    # Формируем URL для GitHub Search API
    search_query = urllib.parse.quote(f"{query} SKILL.md in:path")
    url = f"https://api.github.com/search/code?q={search_query}&per_page={min(max_results, 30)}"

    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-DevCorp/1.0",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", [])[:max_results]:
                repo_info = _extract_repo_info(item)
                if repo_info:
                    results.append(repo_info)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        pass  # Если API недоступен, возвращаем известные репозитории

    return results


def _extract_repo_info(item: dict) -> Optional[dict]:
    """Извлекает информацию о репозитории из результата GitHub API."""
    try:
        repo_url = item.get("repository", {}).get("html_url", "")
        repo_name = item.get("repository", {}).get("full_name", "")
        description = item.get("repository", {}).get("description", "") or ""
        stars = item.get("repository", {}).get("stargazers_count", 0)

        if not repo_name:
            return None

        return {
            "name": repo_name,
            "url": f"{repo_url}.git",
            "description": description,
            "stars": stars,
            "technologies": _detect_technologies(repo_name, description),
        }
    except Exception:
        return None


def _detect_technologies(name: str, description: str) -> list[str]:
    """Определяет технологии по имени и описанию репозитория."""
    techs = set()
    text = f"{name} {description}".lower()

    tech_patterns = {
        "dart": [r'\bdart\b'],
        "flutter": [r'\bflutter\b'],
        "python": [r'\bpython\b'],
        "javascript": [r'\bjavascript\b', r'\bjs\b', r'\btypescript\b'],
        "react": [r'\breact\b'],
        "nodejs": [r'\bnode\b', r'\bnodejs\b'],
        "rust": [r'\brust\b'],
        "go": [r'\bgo\b'],
        "docker": [r'\bdocker\b', r'\bk8s\b', r'\bkubernetes\b'],
        "sql": [r'\bsql\b', r'\bdatabase\b', r'\bpostgres\b'],
        "testing": [r'\btest\b', r'\bpytest\b', r'\bqa\b'],
        "security": [r'\bsecurity\b', r'\bpentest\b'],
        "design": [r'\bdesign\b', r'\bfigma\b', r'\bui\b', r'\bux\b'],
        "devops": [r'\bdevops\b', r'\bci/cd\b'],
        "ml": [r'\bml\b', r'\bmachine.learning\b', r'\bdata\b'],
    }

    for tech, patterns in tech_patterns.items():
        for pat in patterns:
            if re.search(pat, text):
                techs.add(tech)
                break

    return sorted(techs) if techs else ["general"]


def suggest_skills(technologies: list[str] = None) -> list[SkillSuggestion]:
    """Формирует список предложений скилов для установки.

    Анализирует:
    1. Установленные источники (registry.json)
    2. Известные репозитории (KNOWN_SKILL_REPOS)
    3. Результаты поиска на GitHub

    Args:
        technologies: Список технологий для фильтрации.
                      Если None — показывает все известные.

    Returns:
        Список предложений SkillSuggestion
    """
    installed = _get_installed_sources()
    suggestions = []

    # Проверяем известные репозитории
    for key, info in KNOWN_SKILL_REPOS.items():
        if technologies:
            tech_match = any(t.lower() in [x.lower() for x in info["technologies"]] for t in technologies)
            if not tech_match:
                continue

        is_installed = any(
            s["name"] == key
            or s["name"] in info["repo"]
            or key in s["name"]
            or info["repo"].split("/")[-1] in s["name"]
            for s in installed
        )

        suggestions.append(SkillSuggestion(
            name=key,
            repo=info["repo"],
            url=info["url"] or f"https://github.com/{info['repo']}.git",
            description=info["description"],
            departments=info["departments"],
            technologies=info["technologies"],
            is_installed=is_installed,
        ))

    # Если указаны технологии — ищем на GitHub
    if technologies:
        for tech in technologies:
            github_results = search_github_skills(tech, max_results=5)
            for res in github_results:
                name = res["name"].replace("/", "-")
                if not any(s.repo == res["name"] for s in suggestions):
                    depts = _technologies_to_departments(res["technologies"])
                    suggestions.append(SkillSuggestion(
                        name=name,
                        repo=res["name"],
                        url=res["url"],
                        description=res["description"][:200],
                        departments=depts,
                        technologies=res["technologies"],
                        is_installed=False,
                        stars=res["stars"],
                    ))

    return suggestions


def _technologies_to_departments(technologies: list[str]) -> list[str]:
    """Определяет отделы по списку технологий."""
    depts = set()
    for tech in technologies:
        tech_lower = tech.lower()
        if tech_lower in TECH_TO_DEPARTMENT:
            depts.add(TECH_TO_DEPARTMENT[tech_lower])
    if not depts:
        depts.add("development")
    return sorted(depts)


def _get_installed_sources() -> list[dict]:
    """Возвращает список установленных источников."""
    try:
        if REGISTRY_FILE.exists():
            data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            return data.get("sources", [])
    except (json.JSONDecodeError, OSError):
        pass
    return []


def get_all_installed_skills() -> list[dict]:
    """Возвращает список всех установленных внешних скилов.

    Читает как из registry.json, так и сканирует external/ директорию.
    """
    from skills.registry import discover_skills

    skills = discover_skills(source="external")
    return skills


def get_skills_for_department(department: str) -> list[dict]:
    """Возвращает скилы, подходящие для указанного отдела."""
    from skills.registry import search_skills
    return search_skills(department=department, skill_type="all")


def _cli():
    """CLI для discovery.py."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "suggest"

    if cmd == "suggest":
        techs = sys.argv[2:] if len(sys.argv) > 2 else None
        if techs:
            print(f"\n🔍 Поиск скилов для технологий: {', '.join(techs)}\n")
        else:
            print("\n🔍 Все известные источники скилов:\n")

        suggestions = suggest_skills(technologies=techs)
        if not suggestions:
            print("  😕 Ничего не найдено")
            return

        for s in suggestions:
            status = "✅" if s.is_installed else "⬇️"
            depts = ", ".join(s.departments)
            techs_str = ", ".join(s.technologies)
            stars = f" ⭐{s.stars}" if s.stars else ""
            print(f"  {status} {s.name} — {s.description[:100]}{stars}")
            print(f"       отделы: {depts} | технологии: {techs_str}")
            print(f"       {s.repo}")
            if not s.is_installed:
                print(f"       установка: python skills/loader.py install {s.url} {s.name}")
            print()

        installed_count = sum(1 for s in suggestions if s.is_installed)
        print(f"  📊 Найдено: {len(suggestions)} | Установлено: {installed_count} | Доступно: {len(suggestions) - installed_count}")

    elif cmd == "assign":
        dept_name = sys.argv[2] if len(sys.argv) > 2 else ""
        if not dept_name:
            print("❌ Укажите отдел: python skills/discovery.py assign <department>")
            return

        skills = get_skills_for_department(dept_name)
        print(f"\n📋 Скилы для отдела {dept_name}:\n")
        for s in skills:
            meta = s["frontmatter"]
            grade = meta.get("grade", "?")
            icon = "📦" if s.get("skill_type") == "builtin" else "🌐"
            print(f"  {icon} [{grade}] {meta.get('name', '?')} — {meta.get('description', '')[:120]}")
        print(f"\n  Всего: {len(skills)} скилов\n")


if __name__ == "__main__":
    _cli()
