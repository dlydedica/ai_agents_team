"""
Менеджер скилов AI DevCorp.

Отвечает за:
  - Назначение скилов агентам/сотрудникам
  - Работу с профилями (создание, просмотр, применение)
  - Per-project конфигурацию скилов
  - Активацию/деактивацию скилов под проект
"""

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from registry import discover_skills, get_skill, search_skills  # noqa: E402

SKILLS_DIR = Path(__file__).parent
PROFILES_DIR = SKILLS_DIR / "profiles"
CONFIG_DIR = SKILLS_DIR / "project-configs"
BUILTIN_DIR = SKILLS_DIR / "builtin"

# ──────────────────────────────────────────────
# Профили агентов
# ──────────────────────────────────────────────


def list_profiles() -> list[dict]:
    """Список всех доступных профилей."""
    profiles = []
    if not PROFILES_DIR.exists():
        return profiles

    for pf_file in sorted(PROFILES_DIR.glob("*.profile.json")):
        try:
            data = json.loads(pf_file.read_text(encoding="utf-8"))
            data["_file"] = str(pf_file.relative_to(SKILLS_DIR))
            profiles.append(data)
        except (json.JSONDecodeError, OSError):
            pass

    return profiles


def get_profile(name: str) -> Optional[dict]:
    """Получить профиль по имени."""
    for p in list_profiles():
        if p.get("name") == name:
            return p
    return None


def create_profile(
    name: str,
    skills: list[str],
    department: str = "development",
    grade: str = "M",
    description: str = "",
    display_name: str = "",
    tags: list[str] = None,
) -> dict:
    """Создать новый профиль агента.

    Args:
        name: Уникальное имя профиля
        skills: Список имён скилов
        department: Основной отдел
        grade: Грейд (J/M/S/L)
        description: Описание профиля
        display_name: Отображаемое имя
        tags: Теги для поиска
    """
    if get_profile(name):
        return {"error": f"Профиль '{name}' уже существует"}

    # Проверяем, что все скилы существуют
    missing = []
    for skill_name in skills:
        if not get_skill(skill_name):
            missing.append(skill_name)

    profile = {
        "name": name,
        "version": "1.0.0",
        "display_name": display_name or name.replace("_", " ").title(),
        "description": description,
        "skills": skills,
        "departments": [department],
        "grade": grade,
        "tags": tags or [],
        "icon": "👤",
    }

    filepath = PROFILES_DIR / f"{name}.profile.json"
    filepath.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    result = profile.copy()
    if missing:
        result["warning"] = f"Следующие скилы не найдены в реестре: {', '.join(missing)}"

    return result


def resolve_profile_skills(profile_name: str) -> list[dict]:
    """Получить полное содержимое скилов профиля."""
    profile = get_profile(profile_name)
    if not profile:
        return []

    resolved = []
    for skill_name in profile.get("skills", []):
        skill = get_skill(skill_name)
        if skill:
            resolved.append(skill)
    return resolved


# ──────────────────────────────────────────────
# Per-project конфигурация
# ──────────────────────────────────────────────


def list_project_configs() -> list[dict]:
    """Список всех конфигураций проектов."""
    configs = []
    if not CONFIG_DIR.exists():
        return configs

    for cfg_file in sorted(CONFIG_DIR.glob("*.json")):
        if cfg_file.name == "default.json":
            continue
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            configs.append(data)
        except (json.JSONDecodeError, OSError):
            pass

    return configs


def get_project_config(project_name: str) -> Optional[dict]:
    """Получить конфигурацию проекта."""
    cfg_file = CONFIG_DIR / f"{project_name}.json"
    if not cfg_file.exists():
        return None

    try:
        return json.loads(cfg_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def set_project_config(project_name: str, config: dict) -> dict:
    """Создать или обновить конфигурацию проекта."""
    cfg_file = CONFIG_DIR / f"{project_name}.json"
    config["project"] = project_name
    cfg_file.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_active_skills_for_project(project_name: str) -> dict:
    """Получить активные скилы для проекта с учётом overrides.

    Возвращает словарь: имя_агента -> список скилов
    """
    config = get_project_config(project_name)
    if not config:
        return {}

    result = {}
    overrides = config.get("skill_overrides", {})

    for agent_entry in config.get("active_agents", []):
        if isinstance(agent_entry, str):
            agent_name = agent_entry
            profile_name = agent_name  # имя совпадает с профилем
        else:
            agent_name = agent_entry.get("name", "")
            profile_name = agent_entry.get("profile", agent_name)

        # Базовые скилы из профиля
        profile = get_profile(profile_name)
        base_skills = list(profile.get("skills", [])) if profile else []

        # Применяем overrides
        agent_overrides = overrides.get(agent_name, {})
        for add_skill in agent_overrides.get("add", []):
            if add_skill not in base_skills:
                base_skills.append(add_skill)
        for remove_skill in agent_overrides.get("remove", []):
            if remove_skill in base_skills:
                base_skills.remove(remove_skill)

        # Загружаем полные данные скилов
        resolved = []
        for sn in base_skills:
            s = get_skill(sn)
            if s:
                resolved.append(s)

        result[agent_name] = resolved

    return result


# ──────────────────────────────────────────────
# Назначение скилов (CLI / MCP)
# ──────────────────────────────────────────────


def assign_skills_to_agent(
    agent_name: str,
    skills_to_add: list[str] = None,
    skills_to_remove: list[str] = None,
    project: str = "",
) -> dict:
    """Назначить/удалить скилы агенту (опционально для конкретного проекта).

    Если указан project — сохраняет override в конфиг проекта.
    Если project не указан — создаёт/обновляет профиль агента.
    """
    if project:
        config = get_project_config(project) or {
            "description": "",
            "workflow": "default",
            "active_agents": [],
            "skill_overrides": {},
            "external_skills": [],
        }

        if "skill_overrides" not in config:
            config["skill_overrides"] = {}

        if agent_name not in config["skill_overrides"]:
            config["skill_overrides"][agent_name] = {"add": [], "remove": []}

        override = config["skill_overrides"][agent_name]
        if skills_to_add:
            for s in skills_to_add:
                if s not in override["add"]:
                    override["add"].append(s)
        if skills_to_remove:
            for s in skills_to_remove:
                if s not in override["remove"]:
                    override["remove"].append(s)

        # Убираем пересечения
        override["add"] = [s for s in override["add"] if s not in override.get("remove", [])]

        set_project_config(project, config)
        return {"action": "override_saved", "project": project, "agent": agent_name, "override": override}

    else:
        # Работаем напрямую с профилем
        profile = get_profile(agent_name)
        if not profile:
            return {"error": f"Агент '{agent_name}' не найден. Сначала создайте профиль."}

        current_skills = list(profile.get("skills", []))
        if skills_to_add:
            for s in skills_to_add:
                if s not in current_skills:
                    current_skills.append(s)
        if skills_to_remove:
            current_skills = [s for s in current_skills if s not in skills_to_remove]

        profile["skills"] = current_skills
        create_profile(
            name=profile["name"],
            skills=current_skills,
            department=profile.get("departments", ["development"])[0],
            grade=profile.get("grade", "M"),
            description=profile.get("description", ""),
            display_name=profile.get("display_name", ""),
            tags=profile.get("tags", []),
        )
        return {"action": "profile_updated", "agent": agent_name, "skills": current_skills}


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "profiles":
        profiles = list_profiles()
        print(f"👤 Профили агентов ({len(profiles)}):\n")
        for p in profiles:
            skills = ", ".join(p.get("skills", []))
            print(f"  • {p.get('name', '?')} [{p.get('grade', '?')}]")
            print(f"    скилы: {skills}")
            print()

    elif cmd == "profile":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        profile = get_profile(name)
        if profile:
            print(f"👤 Профиль: {profile.get('display_name', name)}")
            print(f"   Имя:     {profile.get('name', '')}")
            print(f"   Грейд:   {profile.get('grade', '')}")
            print(f"   Отдел:   {', '.join(profile.get('departments', []))}")
            print(f"   Скилы:   {', '.join(profile.get('skills', []))}")
        else:
            print(f"❌ Профиль '{name}' не найден")

    elif cmd == "create-profile":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        skills = sys.argv[3].split(",") if len(sys.argv) > 3 else []
        dept = sys.argv[4] if len(sys.argv) > 4 else "development"
        grade = sys.argv[5] if len(sys.argv) > 5 else "M"
        result = create_profile(name, skills, dept, grade)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "projects":
        configs = list_project_configs()
        print(f"📋 Конфигурации проектов ({len(configs)}):\n")
        for c in configs:
            agents = [a.get("name", a) if isinstance(a, dict) else a for a in c.get("active_agents", [])]
            print(f"  • {c.get('project', '?')} — агенты: {', '.join(agents)}")

    elif cmd == "project":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        config = get_project_config(name)
        if config:
            print(json.dumps(config, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Конфигурация проекта '{name}' не найдена")

    elif cmd == "active":
        project = sys.argv[2] if len(sys.argv) > 2 else "default"
        active = get_active_skills_for_project(project)
        print(f"🎯 Активные скилы для проекта '{project}':\n")
        for agent, skills in active.items():
            print(f"  👤 {agent}:")
            for s in skills:
                meta = s.get("frontmatter", {})
                print(f"     • {meta.get('name', '?')} [{meta.get('grade', '?')}] — {meta.get('description', '')}")
            print()

    else:
        print("Команды:")
        print("  profiles                    — список профилей")
        print("  profile <name>             — детали профиля")
        print("  create-profile <name> <skills,csv> [dept] [grade]")
        print("  projects                   — список проектов")
        print("  project <name>             — конфиг проекта")
        print("  active <project>           — активные скилы для проекта")
