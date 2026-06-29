"""
Сканер проектов для автоматического обнаружения технологий и подбора скилов.

Анализирует файлы проекта (pubspec.yaml, requirements.txt, package.json и др.)
и определяет стек технологий, чтобы предложить подходящие скилы.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# --- Определения для распознавания ---

# Маппинг: имя зависимости → технология
DEP_TO_TECH = {
    # Python
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "pydantic": "pydantic",
    "pytest": "pytest",
    "celery": "celery",
    "redis": "redis",
    "httpx": "httpx",
    "requests": "requests",
    "aiohttp": "aiohttp",
    "graphene": "graphql",
    "tortoise-orm": "tortoise-orm",
    "beanie": "beanie",
    "motor": "motor",
    "numpy": "numpy",
    "pandas": "pandas",
    "scikit-learn": "scikit-learn",
    "tensorflow": "tensorflow",
    "torch": "pytorch",
    "jupyter": "jupyter",
    "streamlit": "streamlit",
    # Flutter / Dart
    "flutter": "flutter",
    "dart": "dart",
    "riverpod": "riverpod",
    "bloc": "bloc",
    "provider": "provider",
    "go_router": "go_router",
    "dio": "dio",
    "drift": "drift",
    "isar": "isar",
    "hive": "hive",
    "freezed": "freezed",
    "json_serializable": "json_serializable",
    "firebase_core": "firebase",
    "firestore": "firestore",
    "cached_network_image": "cached_network_image",
    "flutter_secure_storage": "flutter_secure_storage",
    # JavaScript / TypeScript
    "react": "react",
    "next": "nextjs",
    "vue": "vue",
    "angular": "angular",
    "express": "express",
    "nest": "nestjs",
    "typescript": "typescript",
    "prisma": "prisma",
    "typeorm": "typeorm",
    "mongoose": "mongoose",
    "jest": "jest",
    "vitest": "vitest",
    "playwright": "playwright",
    "cypress": "cypress",
    # Базы данных
    "mysql": "mysql",
    "pymysql": "mysql",
    "postgresql": "postgresql",
    "psycopg2": "postgresql",
    "asyncpg": "postgresql",
    "sqlite": "sqlite",
    "mongodb": "mongodb",
    "pymongo": "mongodb",
    # DevOps
    "docker": "docker",
    "docker-compose": "docker",
    "kubernetes": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "github-actions": "ci/cd",
    # Другое
    "geoip2": "geoip",
    "jinja2": "jinja2",
    "uvicorn": "uvicorn",
}

# Маппинг: технология → отдел
TECH_TO_DEPARTMENT = {
    "fastapi": "development",
    "flask": "development",
    "django": "development",
    "sqlalchemy": "development",
    "alembic": "development",
    "pydantic": "development",
    "pytest": "qa",
    "celery": "development",
    "redis": "development",
    "httpx": "development",
    "graphql": "development",
    "python": "development",
    "flutter": "development",
    "dart": "development",
    "riverpod": "development",
    "bloc": "development",
    "provider": "development",
    "go_router": "development",
    "dio": "development",
    "drift": "development",
    "isar": "development",
    "hive": "development",
    "firebase": "development",
    "react": "development",
    "nextjs": "development",
    "vue": "development",
    "angular": "development",
    "express": "development",
    "nestjs": "development",
    "typescript": "development",
    "mysql": "data",
    "postgresql": "data",
    "mongodb": "data",
    "sqlite": "data",
    "docker": "devops",
    "kubernetes": "devops",
    "terraform": "devops",
    "ansible": "devops",
    "ci/cd": "devops",
    "jest": "qa",
    "vitest": "qa",
    "playwright": "qa",
    "cypress": "qa",
    "pytorch": "data",
    "tensorflow": "data",
    "numpy": "data",
    "pandas": "data",
    "jupyter": "data",
}

# Маппинг: категория технологии → теги для поиска скилов
TECH_TO_SEARCH_TAGS = {
    "python": ["python", "python-backend"],
    "fastapi": ["python", "fastapi"],
    "django": ["python", "django"],
    "flask": ["python", "flask"],
    "flutter": ["flutter", "dart"],
    "dart": ["dart", "flutter"],
    "react": ["react", "frontend"],
    "vue": ["vue", "frontend"],
    "angular": ["angular", "frontend"],
    "typescript": ["typescript", "frontend"],
    "nodejs": ["nodejs", "backend"],
    "docker": ["docker", "devops"],
    "kubernetes": ["kubernetes", "devops"],
    "ci/cd": ["ci-cd", "github-actions"],
    "mysql": ["sql", "mysql", "database"],
    "postgresql": ["sql", "postgresql", "database"],
    "mongodb": ["mongodb", "database"],
    "testing": ["testing", "pytest", "qa"],
    "pytest": ["pytest", "testing"],
    "redis": ["redis", "cache"],
}


@dataclass
class ProjectTech:
    """Обнаруженная технология в проекте."""
    name: str
    category: str  # python, flutter, javascript, devops, database
    source_file: str  # какой файл указал
    confidence: float = 1.0


@dataclass
class ScanResult:
    """Результат сканирования проекта."""
    project_path: str
    project_name: str
    technologies: list[ProjectTech]
    categories: list[str]


# --- Парсеры файлов ---


def _parse_pubspec_yaml(path: Path) -> list[str]:
    """Парсит pubspec.yaml — извлекает зависимости Flutter/Dart."""
    deps = []
    try:
        content = path.read_text(encoding="utf-8")
        in_deps = False
        in_dev_deps = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("dependencies:"):
                in_deps = True
                in_dev_deps = False
                continue
            if stripped.startswith("dev_dependencies:"):
                in_dev_deps = True
                in_deps = False
                continue
            if in_deps or in_dev_deps:
                if stripped.startswith("#") or stripped == "":
                    continue
                # Проверяем, не закончилась ли секция
                if not stripped.startswith("- ") and not stripped[0].isalpha() and not stripped[0].isprintable():
                    # Строка без отступа — конец секции
                    if not stripped.startswith(" ") and ":" not in stripped:
                        in_deps = False
                        in_dev_deps = False
                        continue
                # Извлекаем имя пакета
                match = re.match(r'^(\S+):', stripped)
                if match:
                    deps.append(match.group(1).strip())
    except Exception:
        pass
    return deps


def _parse_requirements_txt(path: Path) -> list[str]:
    """Парсит requirements.txt — извлекает Python-зависимости."""
    deps = []
    try:
        for line in path.read_text(encoding="utf-8").split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                # Извлекаем имя пакета: package==версия или package>=версия
                match = re.match(r'^([a-zA-Z0-9_.-]+)', stripped)
                if match:
                    deps.append(match.group(1).lower().strip("-_."))
    except Exception:
        pass
    return deps


def _parse_package_json(path: Path) -> list[str]:
    """Парсит package.json — извлекает JS/TS-зависимости."""
    deps = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for dep_name in data.get(section, {}):
                # Извлекаем чистое имя (без @scope/)
                clean = dep_name.split("/")[-1].lower().strip("-_.")
                deps.append(clean)
    except Exception:
        pass
    return deps


def _parse_go_mod(path: Path) -> list[str]:
    """Парсит go.mod — извлекает Go-зависимости."""
    deps = []
    try:
        for line in path.read_text(encoding="utf-8").split("\n"):
            stripped = line.strip()
            if stripped.startswith("require (") or stripped == "require":
                continue
            if stripped.startswith(")"):
                continue
            if stripped and not stripped.startswith("//"):
                match = re.match(r'^([a-zA-Z0-9_./-]+)\s', stripped)
                if match:
                    deps.append(match.group(1).split("/")[0].lower())
    except Exception:
        pass
    return deps


def _detect_flutter(path: Path) -> list[ProjectTech]:
    """Ищет Flutter-проекты в директории."""
    results = []
    for pubspec in path.rglob("pubspec.yaml"):
        try:
            relative = pubspec.relative_to(path)
        except ValueError:
            relative = pubspec
        results.append(ProjectTech(
            name="flutter",
            category="flutter",
            source_file=str(relative),
        ))
        deps = _parse_pubspec_yaml(pubspec)
        for dep in deps:
            if dep in DEP_TO_TECH:
                tech_name = DEP_TO_TECH[dep]
                results.append(ProjectTech(
                    name=tech_name,
                    category="flutter",
                    source_file=str(relative),
                ))
        results.append(ProjectTech(
            name="dart",
            category="flutter",
            source_file=str(relative),
        ))
    return results


def _detect_python(path: Path) -> list[ProjectTech]:
    """Ищет Python-проекты."""
    results = []

    # Ищем requirements.txt
    for req_file in path.rglob("requirements.txt"):
        try:
            relative = req_file.relative_to(path)
        except ValueError:
            relative = req_file
        results.append(ProjectTech(
            name="python",
            category="python",
            source_file=str(relative),
        ))
        deps = _parse_requirements_txt(req_file)
        for dep in deps:
            if dep in DEP_TO_TECH:
                tech_name = DEP_TO_TECH[dep]
                results.append(ProjectTech(
                    name=tech_name,
                    category="python",
                    source_file=str(relative),
                ))

    # Ищем setup.py / pyproject.toml
    for cfg_file in path.rglob("setup.py"):
        try:
            relative = cfg_file.relative_to(path)
        except ValueError:
            relative = cfg_file
        if "python" not in [t.name for t in results]:
            results.append(ProjectTech(
                name="python",
                category="python",
                source_file=str(relative),
            ))

    for cfg_file in path.rglob("pyproject.toml"):
        try:
            content = cfg_file.read_text(encoding="utf-8")
            if "[tool.poetry]" in content or "[project]" in content or "[build-system]" in content:
                relative = cfg_file.relative_to(path)
                if "python" not in [t.name for t in results]:
                    results.append(ProjectTech(
                        name="python",
                        category="python",
                        source_file=str(relative),
                    ))
        except Exception:
            pass

    return results


def _detect_javascript(path: Path) -> list[ProjectTech]:
    """Ищет JavaScript/TypeScript-проекты."""
    results = []
    for pkg_file in path.rglob("package.json"):
        # Пропускаем node_modules
        if "node_modules" in pkg_file.parts:
            continue
        try:
            relative = pkg_file.relative_to(path)
        except ValueError:
            relative = pkg_file
        deps = _parse_package_json(pkg_file)
        for dep in deps:
            if dep in DEP_TO_TECH:
                tech_name = DEP_TO_TECH[dep]
                results.append(ProjectTech(
                    name=tech_name,
                    category="javascript",
                    source_file=str(relative),
                ))
        # Определяем язык
        has_ts = any("typescript" in d for d in deps)
        results.append(ProjectTech(
            name="typescript" if has_ts else "javascript",
            category="javascript",
            source_file=str(relative),
        ))
    return results


def _detect_go(path: Path) -> list[ProjectTech]:
    """Ищет Go-проекты."""
    results = []
    for mod_file in path.rglob("go.mod"):
        try:
            relative = mod_file.relative_to(path)
        except ValueError:
            relative = mod_file
        results.append(ProjectTech(
            name="go",
            category="go",
            source_file=str(relative),
        ))
    return results


def _detect_devops(path: Path) -> list[ProjectTech]:
    """Ищет DevOps-конфигурацию."""
    results = []
    for dockerfile in path.rglob("Dockerfile"):
        try:
            relative = dockerfile.relative_to(path)
        except ValueError:
            relative = dockerfile
        if "docker" not in [t.name for t in results]:
            results.append(ProjectTech(
                name="docker",
                category="devops",
                source_file=str(relative),
            ))

    for compose in path.rglob("docker-compose.yml"):
        try:
            relative = compose.relative_to(path)
        except ValueError:
            relative = compose
        if "docker" not in [t.name for t in results]:
            results.append(ProjectTech(
                name="docker",
                category="devops",
                source_file=str(relative),
            ))

    # GitHub Actions
    for workflow in Path(path).rglob(".github/workflows/*.yml"):
        try:
            relative = workflow.relative_to(path)
        except ValueError:
            relative = workflow
        results.append(ProjectTech(
            name="ci/cd",
            category="devops",
            source_file=str(relative),
        ))

    return results


# --- Основной сканер ---


def scan_project(project_path: str) -> ScanResult:
    """Сканирует проект и возвращает обнаруженный стек технологий.

    Args:
        project_path: Путь к корню проекта

    Returns:
        ScanResult с найденными технологиями
    """
    path = Path(project_path).resolve()

    if not path.exists() or not path.is_dir():
        return ScanResult(
            project_path=project_path,
            project_name=path.name,
            technologies=[],
            categories=[],
        )

    all_techs = []
    all_techs.extend(_detect_flutter(path))
    all_techs.extend(_detect_python(path))
    all_techs.extend(_detect_javascript(path))
    all_techs.extend(_detect_go(path))
    all_techs.extend(_detect_devops(path))

    # Дедупликация
    seen = set()
    unique = []
    for tech in all_techs:
        key = (tech.name, tech.category)
        if key not in seen:
            seen.add(key)
            unique.append(tech)
        else:
            # Обновляем source_file, если нашли в другом месте
            for existing in unique:
                if (existing.name, existing.category) == key:
                    if tech.source_file not in existing.source_file:
                        existing.source_file += f", {tech.source_file}"
                    break

    categories = sorted(set(t.category for t in unique))

    return ScanResult(
        project_path=str(path),
        project_name=path.name,
        technologies=unique,
        categories=categories,
    )


def technologies_to_search_tags(technologies: list[ProjectTech]) -> list[str]:
    """Преобразует найденные технологии в теги для поиска скилов.

    Args:
        technologies: Список технологий из ScanResult

    Returns:
        Список поисковых тегов
    """
    tags = set()
    for tech in technologies:
        name = tech.name.lower()
        if name in TECH_TO_SEARCH_TAGS:
            for tag in TECH_TO_SEARCH_TAGS[name]:
                tags.add(tag)
        else:
            tags.add(name)
    return sorted(tags)


def auto_extend_known_repos(technologies: list[ProjectTech]) -> dict:
    """Анализирует, какие технологии покрыты скилами, и ищет новые на GitHub.

    Args:
        technologies: Список технологий из ScanResult

    Returns:
        dict с ключами:
          - covered: технологии, для которых есть скилы
          - uncovered: технологии без скилов
          - github_found: найденные на GitHub репозитории
          - github_error: ошибка GitHub API (если была)
          - suggestions: список словарей-предложений для known_repos.json
    """
    tech_names = set(t.name.lower() for t in technologies)

    from skills.discovery import KNOWN_SKILL_REPOS, search_github_skills

    # Какие технологии покрыты известными репозиториями
    covered_techs = set()
    for info in KNOWN_SKILL_REPOS.values():
        for tech in info.get("technologies", []):
            if tech.lower() in tech_names:
                covered_techs.add(tech.lower())

    uncovered = sorted(tech_names - covered_techs)
    covered = sorted(tech_names & covered_techs)

    suggestions = []
    github_error = None
    github_found = []

    # Для непокрытых технологий пытаемся найти скилы на GitHub
    for tech_name in uncovered:
        try:
            results = search_github_skills(tech_name, max_results=3)
            if results:
                for res in results:
                    repo_short = res["name"]
                    key = repo_short.replace("/", "-").lower()

                    # Проверяем, нет ли уже такого репозитория в known
                    already_known = False
                    for info in KNOWN_SKILL_REPOS.values():
                        if info["repo"].lower() == repo_short.lower():
                            already_known = True
                            break
                    if already_known:
                        continue

                    from skills.discovery import _technologies_to_departments
                    depts = _technologies_to_departments(res["technologies"])

                    suggestions.append({
                        "key": key,
                        "repo": repo_short,
                        "url": res["url"],
                        "description": res.get("description", f"Скилы по {tech_name}")[:200],
                        "departments": depts,
                        "technologies": res.get("technologies", [tech_name]),
                        "stars": res.get("stars", 0),
                        "source": "auto-detected",
                    })
                    github_found.append(tech_name)
        except Exception as e:
            github_error = str(e)

    return {
        "covered": covered,
        "uncovered": uncovered,
        "github_found": github_found,
        "github_error": github_error,
        "suggestions": suggestions,
    }


# CLI
def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"

    if cmd == "scan":
        project_path = sys.argv[2] if len(sys.argv) > 2 else "."
        print(f"\n🔍 Сканирование проекта: {project_path}\n")

        result = scan_project(project_path)
        if not result.technologies:
            print("  😕 Технологии не обнаружены\n")
            return

        print(f"  📁 Проект: {result.project_name}\n")
        print(f"  📊 Стек технологий:\n")

        for cat in result.categories:
            techs = [t for t in result.technologies if t.category == cat]
            print(f"  [{cat.upper()}]")
            for t in techs:
                print(f"     ✅ {t.name:25s} ({t.source_file})")
            print()

        # Показываем теги для поиска скилов
        tags = technologies_to_search_tags(result.technologies)
        print(f"  🏷️  Теги для поиска скилов: {', '.join(tags)}\n")
        print(f"  💡 python team.py skills suggest {' '.join(tags)}\n")

        # Предлагаем расширение known_repos
        suggestions = auto_extend_known_repos(result.technologies)
        if suggestions:
            print(f"  🌐 Найдено новых репозиториев со скилами ({len(suggestions)}):\n")
            for s in sorted(suggestions, key=lambda x: -x["stars"])[:5]:
                depts = ", ".join(s["departments"])
                print(f"     ⭐{s['stars']} {s['key']} — {s['description'][:80]}")
                print(f"        отделы: {depts}")
                print(f"        установка: python team.py skills install {s['url']}")
                print()

    elif cmd == "suggest":
        project_path = sys.argv[2] if len(sys.argv) > 2 else "."

        result = scan_project(project_path)
        if not result.technologies:
            print("  😕 Технологии не обнаружены\n")
            return

        tags = technologies_to_search_tags(result.technologies)
        print(f"\n🔍 Теги для поиска: {' '.join(tags)}\n")
        print(f"💡 python team.py skills suggest {' '.join(tags)}\n")


if __name__ == "__main__":
    _cli()
