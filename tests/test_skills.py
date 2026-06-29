"""
Тесты для библиотеки скилов AI DevCorp.

Запуск:
    python -m pytest skills/test_skills.py -v
"""

import json
import sys
import os
from pathlib import Path

# Добавляем skills/ в путь
sys.path.insert(0, str(Path(__file__).parent))

from registry import (
    discover_skills, search_skills, get_skill,
    validate_all, generate_manifest, write_manifest,
)
from manager import (
    list_profiles, get_profile, create_profile,
    list_project_configs, get_project_config, set_project_config,
    get_active_skills_for_project, assign_skills_to_agent,
)


# ══════════════════════════════════════════════
# Тесты registry.py
# ══════════════════════════════════════════════


def test_discover_all_skills():
    """Проверка: все .skill.md файлы найдены."""
    skills = discover_skills()
    assert len(skills) >= 20, f"Ожидалось >=20 скилов, найдено {len(skills)}"
    # Проверяем, что все имеют корректный фронтматер
    for s in skills:
        meta = s["frontmatter"]
        assert "name" in meta, f"Скил без name: {s.get('filepath', '?')}"
        assert "grade" in meta, f"Скил без grade: {meta.get('name', '?')}"
        assert meta["grade"] in ("J", "M", "S", "L"), f"Некорректный grade: {meta['grade']}"
        assert "departments" in meta, f"Скил без departments: {meta.get('name', '?')}"


def test_discover_builtin_only():
    """Проверка: только builtin скилы."""
    skills = discover_skills(source="builtin")
    assert len(skills) >= 20
    for s in skills:
        assert s.get("skill_type") == "builtin"


def test_discover_external_empty():
    """Проверка: external скилы пока пусты."""
    skills = discover_skills(source="external")
    assert len(skills) == 0


def test_search_by_name():
    """Проверка: поиск по имени."""
    results = search_skills(query="python_backend")
    assert len(results) >= 1
    assert any("python_backend" in r["frontmatter"].get("name", "") for r in results)


def test_search_by_department():
    """Проверка: поиск по отделу."""
    results = search_skills(department="development")
    assert len(results) >= 5, f"Ожидалось >=5 скилов, найдено {len(results)}"
    for r in results:
        assert "development" in r["frontmatter"].get("departments", [])


def test_search_by_grade():
    """Проверка: поиск по грейду."""
    results = search_skills(grade="S")
    assert len(results) >= 3, f"Ожидалось >=3 Senior скилов, найдено {len(results)}"
    for r in results:
        assert r["frontmatter"].get("grade") == "S"


def test_search_by_tags():
    """Проверка: поиск по тегам."""
    results = search_skills(tags=["python"])
    assert len(results) >= 3, f"Ожидалось >=3 скилов с тегом python, найдено {len(results)}"


def test_get_skill_by_name():
    """Проверка: получение скила по имени."""
    skill = get_skill("python_backend")
    assert skill is not None
    assert skill["frontmatter"]["name"] == "python_backend"
    assert "body" in skill
    assert len(skill["body"]) > 50  # тело скила не пустое


def test_get_skill_not_found():
    """Проверка: несуществующий скил."""
    skill = get_skill("nonexistent_skill_xyz")
    assert skill is None


def test_validate_all_skills():
    """Проверка: все скилы валидны."""
    errors = validate_all()
    assert len(errors) == 0, f"Найдены ошибки: {errors}"


def test_generate_manifest():
    """Проверка: генерация manifest.json."""
    manifest = generate_manifest()
    assert manifest["total"] >= 20
    assert manifest["by_type"]["builtin"] >= 20
    assert manifest["by_type"]["external"] == 0
    assert len(manifest["skills"]) >= 20
    # Проверяем структуру записи в манифесте
    for entry in manifest["skills"]:
        assert "name" in entry
        assert "grade" in entry
        assert "departments" in entry


# ══════════════════════════════════════════════
# Тесты manager.py
# ══════════════════════════════════════════════


def test_list_profiles():
    """Проверка: список профилей."""
    profiles = list_profiles()
    assert len(profiles) >= 8, f"Ожидалось >=8 профилей, найдено {len(profiles)}"
    for p in profiles:
        assert "name" in p
        assert "skills" in p
        assert len(p["skills"]) >= 1


def test_get_profile_exists():
    """Проверка: получение существующего профиля."""
    profile = get_profile("tech_lead")
    assert profile is not None
    assert profile["name"] == "tech_lead"
    assert "python_backend" in profile["skills"]
    assert profile["grade"] in ("J", "M", "S", "L")


def test_get_profile_not_found():
    """Проверка: несуществующий профиль."""
    profile = get_profile("nonexistent_profile_xyz")
    assert profile is None


def test_create_profile():
    """Проверка: создание нового профиля."""
    # Сначала удаляем если уже есть от предыдущего теста
    existing = get_profile("test_profile")
    if existing:
        (Path(__file__).parent / "profiles" / "test_profile.profile.json").unlink()

    result = create_profile(
        name="test_profile",
        skills=["python_backend", "react_frontend"],
        department="development",
        grade="M",
        description="Test profile",
    )
    assert "error" not in result
    assert result["name"] == "test_profile"
    assert result["skills"] == ["python_backend", "react_frontend"]

    # Проверяем, что профиль сохранился
    profile = get_profile("test_profile")
    assert profile is not None

    # Очищаем
    (Path(__file__).parent / "profiles" / "test_profile.profile.json").unlink()


def test_create_duplicate_profile():
    """Проверка: создание дубликата профиля."""
    result = create_profile(
        name="tech_lead",
        skills=["python_backend"],
        department="development",
        grade="S",
    )
    assert "error" in result
    assert "уже существует" in result["error"]


def test_list_project_configs():
    """Проверка: список конфигураций проектов."""
    configs = list_project_configs()
    assert len(configs) >= 2, f"Ожидалось >=2 конфигов, найдено {len(configs)}"


def test_get_project_config():
    """Проверка: получение конфига проекта."""
    config = get_project_config("ml-platform")
    assert config is not None
    assert config["project"] == "ml-platform"
    assert "active_agents" in config
    assert "skill_overrides" in config


def test_get_project_config_not_found():
    """Проверка: несуществующий проект."""
    config = get_project_config("nonexistent_project_xyz")
    assert config is None


def test_set_project_config():
    """Проверка: создание/обновление конфига проекта."""
    test_config = {
        "description": "Test project",
        "workflow": "emergency",
        "active_agents": ["tech_lead", "qa_automation"],
        "skill_overrides": {},
        "external_skills": [],
    }
    result = set_project_config("test_project", test_config)
    assert result["project"] == "test_project"

    # Проверяем, что сохранилось
    config = get_project_config("test_project")
    assert config is not None
    assert len(config["active_agents"]) == 2

    # Очищаем
    (Path(__file__).parent / "project-configs" / "test_project.json").unlink()


def test_get_active_skills():
    """Проверка: активные скилы для проекта."""
    active = get_active_skills_for_project("ml-platform")
    assert len(active) >= 3, f"Ожидалось >=3 агентов, получено {len(active)}"
    # ml_engineer должен иметь fastapi_api (из skill_overrides.add)
    ml_skills = [s["frontmatter"]["name"] for s in active.get("ml_engineer", [])]
    assert "fastapi_api" in ml_skills, f"fastapi_api не найден в ml_engineer: {ml_skills}"


def test_assign_skills_to_agent_project():
    """Проверка: назначение скилов агенту в проекте."""
    # Создаём временный конфиг
    test_config = {
        "description": "Test",
        "workflow": "default",
        "active_agents": ["tech_lead"],
        "skill_overrides": {},
        "external_skills": [],
    }
    set_project_config("test_assign", test_config)

    result = assign_skills_to_agent(
        agent_name="tech_lead",
        skills_to_add=["fastapi_api", "docker_k8s"],
        project="test_assign",
    )
    assert result["action"] == "override_saved"
    assert "fastapi_api" in result["override"]["add"]

    # Очищаем
    (Path(__file__).parent / "project-configs" / "test_assign.json").unlink()


# ══════════════════════════════════════════════
# Тесты loader.py
# ══════════════════════════════════════════════


def test_list_external_sources():
    """Проверка: список внешних источников (из registry.json)."""
    from loader import list_external_sources
    sources = list_external_sources()
    assert isinstance(sources, list)


# ══════════════════════════════════════════════
# Интеграционные тесты
# ══════════════════════════════════════════════


def test_skill_profile_consistency():
    """Проверка: все скилы из профилей существуют в реестре."""
    profiles = list_profiles()
    all_skills = {s["frontmatter"]["name"] for s in discover_skills()}

    missing = []
    for p in profiles:
        for skill_name in p.get("skills", []):
            if skill_name not in all_skills:
                missing.append(f"{p['name']}: {skill_name}")

    assert len(missing) == 0, f"Скилы из профилей не найдены в реестре: {missing}"


def test_dashboard_skills_data():
    """Проверка: данные для дашборда корректно формируются."""
    import subprocess, sys as _sys
    _TEAM_DIR = str(Path(__file__).resolve().parent.parent)

    # Пишем временный скрипт (чтобы избежать проблем с кавычками в PowerShell)
    _script = Path(__file__).parent / "_test_dash_temp.py"
    _script.write_text(f"""
import sys
sys.path.insert(0, {repr(_TEAM_DIR + '/dashboard')})
sys.path.insert(0, {repr(_TEAM_DIR + '/skills')})
from app import _load_skills_data
data = _load_skills_data()
assert data["total_skills"] >= 20, f"skills: {{data['total_skills']}}"
assert data["total_profiles"] >= 8, f"profiles: {{data['total_profiles']}}"
assert len(data["by_department"]) >= 10, f"depts: {{len(data['by_department'])}}"
assert len(data["profiles"]) >= 8, f"profiles list: {{len(data['profiles'])}}"
assert sum(data["by_grade"].values()) == data["total_skills"], f"grades sum mismatch"
print("OK")
""", encoding="utf-8")

    result = subprocess.run(
        [_sys.executable, str(_script)],
        capture_output=True, text=True, timeout=15,
    )
    _script.unlink(missing_ok=True)
    assert result.returncode == 0, f"FAILED: {result.stderr.strip() or result.stdout.strip()}"
    assert "OK" in result.stdout
