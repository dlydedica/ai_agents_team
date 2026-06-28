"""
Реестр скилов AI DevCorp.

Отвечает за:
  - Сканирование .skill.md файлов в builtin/ и external/
  - Поиск и фильтрацию по отделам, грейдам, тегам
  - Генерацию manifest.json (индекс всех скилов)
  - Валидацию скилов (структура, обязательные поля)
"""

import os
import json
import re
from pathlib import Path
from typing import Optional

SKILLS_DIR = Path(__file__).parent
BUILTIN_DIR = SKILLS_DIR / "builtin"
EXTERNAL_DIR = SKILLS_DIR / "external"
MANIFEST_FILE = SKILLS_DIR / "manifest.json"

# Обязательные поля YAML-фронтматера скила
REQUIRED_FRONTMATTER_FIELDS = {"name", "version", "description", "author", "type", "grade"}

VALID_TYPES = {"builtin", "external"}
VALID_GRADES = {"J", "M", "S", "L"}
VALID_DEPARTMENTS = {
    "product", "architecture", "development", "qa", "devops",
    "design", "docs", "hr", "security", "data", "rd", "legal", "marketing",
}


def _parse_skill_file(filepath: Path) -> Optional[dict]:
    """Парсит .skill.md файл, извлекая YAML-фронтматер."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    # Ищем YAML-фронтматер: --- ... ---
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None

    yaml_text = fm_match.group(1)
    meta = {}

    for line in yaml_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            # Многострочные списки (начинаются с -)
            if value == "" or value == "[]":
                meta[key] = []
            elif value.startswith("[") and value.endswith("]"):
                # [a, b, c]
                meta[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
            elif value.startswith('"') and value.endswith('"'):
                meta[key] = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                meta[key] = value[1:-1]
            else:
                meta[key] = value

    # Извлекаем тело скила (после ---)
    body_start = fm_match.end()
    body = content[body_start:].strip()

    return {
        "filepath": str(filepath.relative_to(SKILLS_DIR)),
        "frontmatter": meta,
        "body": body,
    }


def _validate_skill(skill: dict) -> list[str]:
    """Валидирует скил, возвращает список ошибок."""
    errors = []
    meta = skill["frontmatter"]

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in meta:
            errors.append(f"Отсутствует обязательное поле '{field}'")

    if "type" in meta and meta["type"] not in VALID_TYPES:
        errors.append(f"Некорректный type: {meta['type']} (ожидается builtin или external)")

    if "grade" in meta and meta["grade"] not in VALID_GRADES:
        errors.append(f"Некорректный grade: {meta['grade']} (ожидается J/M/S/L)")

    depts = meta.get("departments", [])
    if isinstance(depts, list):
        for d in depts:
            if d not in VALID_DEPARTMENTS:
                errors.append(f"Неизвестный отдел '{d}' в departments")

    return errors


def discover_skills(source: str = "all") -> list[dict]:
    """Сканирует все .skill.md файлы и возвращает список скилов.

    Args:
        source: "builtin" — только свои, "external" — только внешние, "all" — все
    """
    skills = []

    if source in ("all", "builtin") and BUILTIN_DIR.exists():
        for skill_file in sorted(BUILTIN_DIR.rglob("*.skill.md")):
            skill = _parse_skill_file(skill_file)
            if skill:
                skill["skill_type"] = "builtin"
                errors = _validate_skill(skill)
                if errors:
                    skill["_validation_errors"] = errors
                skills.append(skill)

    if source in ("all", "external") and EXTERNAL_DIR.exists():
        for skill_file in sorted(EXTERNAL_DIR.rglob("*.skill.md")):
            skill = _parse_skill_file(skill_file)
            if skill:
                skill["skill_type"] = "external"
                errors = _validate_skill(skill)
                if errors:
                    skill["_validation_errors"] = errors
                skills.append(skill)

    return skills


def search_skills(
    query: str = "",
    department: str = "",
    grade: str = "",
    tags: list[str] = None,
    skill_type: str = "all",
) -> list[dict]:
    """Поиск скилов с фильтрацией.

    Args:
        query: Текстовый поиск по имени/описанию
        department: Фильтр по отделу
        grade: Фильтр по грейду (J/M/S/L)
        tags: Фильтр по тегам
        skill_type: "builtin", "external" или "all"
    """
    skills = discover_skills(source=skill_type)
    query = query.lower().strip()

    results = []
    for skill in skills:
        meta = skill["frontmatter"]
        name = meta.get("name", "").lower()
        desc = meta.get("description", "").lower()
        depts = meta.get("departments", [])
        skill_grade = meta.get("grade", "")
        skill_tags = meta.get("tags", [])

        # Текстовый поиск (имя, описание, теги)
        tags_text = " ".join(skill_tags) if isinstance(skill_tags, list) else ""
        if query and query not in name and query not in desc and query not in tags_text:
            continue

        # Фильтр по отделу
        if department and department not in depts:
            continue

        # Фильтр по грейду
        if grade and skill_grade != grade:
            continue

        # Фильтр по тегам
        if tags:
            skill_tag_set = {t.lower() for t in (skill_tags if isinstance(skill_tags, list) else [])}
            if not any(t.lower() in skill_tag_set for t in tags):
                continue

        results.append(skill)

    return results


def get_skill(name: str) -> Optional[dict]:
    """Получить скил по имени."""
    skills = discover_skills()
    for skill in skills:
        if skill["frontmatter"].get("name") == name:
            return skill
    return None


def generate_manifest() -> dict:
    """Генерирует manifest.json — полный индекс всех скилов."""
    skills = discover_skills()
    manifest = {
        "$schema": "v1",
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "total": len(skills),
        "by_type": {"builtin": 0, "external": 0},
        "by_department": {},
        "by_grade": {},
        "skills": [],
    }

    for skill in skills:
        meta = skill["frontmatter"]
        skill_type = skill.get("skill_type", "builtin")
        manifest["by_type"][skill_type] = manifest["by_type"].get(skill_type, 0) + 1

        for dept in meta.get("departments", []):
            manifest["by_department"][dept] = manifest["by_department"].get(dept, 0) + 1

        grade = meta.get("grade", "")
        if grade:
            manifest["by_grade"][grade] = manifest["by_grade"].get(grade, 0) + 1

        manifest["skills"].append({
            "name": meta.get("name", ""),
            "version": meta.get("version", ""),
            "display_name": meta.get("display_name", ""),
            "description": meta.get("description", ""),
            "type": skill_type,
            "grade": grade,
            "tags": meta.get("tags", []),
            "departments": meta.get("departments", []),
            "filepath": skill.get("filepath", ""),
        })

    return manifest


def write_manifest(manifest: dict = None):
    """Записывает manifest.json на диск."""
    if manifest is None:
        manifest = generate_manifest()
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def validate_all() -> list[dict]:
    """Валидирует все скилы, возвращает список ошибок."""
    skills = discover_skills()
    all_errors = []
    for skill in skills:
        errors = skill.get("_validation_errors", [])
        if errors:
            all_errors.append({
                "file": skill.get("filepath", ""),
                "name": skill["frontmatter"].get("name", "?"),
                "errors": errors,
            })
    return all_errors


# CLI
if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        skills = discover_skills()
        print(f"📚 Всего скилов: {len(skills)}\n")
        for s in skills:
            meta = s["frontmatter"]
            icon = "📦" if s.get("skill_type") == "builtin" else "🌐"
            grade = meta.get("grade", "?")
            depts = ", ".join(meta.get("departments", []))
            tags = ", ".join(meta.get("tags", []))
            print(f"  {icon} [{grade}] {meta.get('name', '?')} — {meta.get('description', '')}")
            print(f"       отделы: {depts} | теги: {tags}")
            print()

    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = search_skills(query=query)
        print(f"🔍 Результатов по запросу '{query}': {len(results)}\n")
        for s in results:
            meta = s["frontmatter"]
            print(f"  • {meta.get('name', '?')} — {meta.get('description', '')}")

    elif cmd == "validate":
        errors = validate_all()
        if errors:
            print(f"⚠️  Найдено ошибок: {len(errors)}\n")
            for e in errors:
                print(f"  ❌ {e['file']}: {', '.join(e['errors'])}")
        else:
            print("✅ Все скилы валидны!")

    elif cmd == "manifest":
        manifest = generate_manifest()
        print(json.dumps(manifest, indent=2, ensure_ascii=False))

    else:
        print("Команды: list, search <query>, validate, manifest")
