#!/usr/bin/env python3
"""
Скрипт обновления AI Agents Team в существующем проекте.

Использование:
    python update.py <путь_к_целевому_проекту> [--dry-run]

Что делает:
    1. Определяет способ подключения ai_agents_team (submodule / копия / симлинк)
    2. Обновляет файлы ai_agents_team (git pull / re-copy)
    3. Обновляет .vscode/mcp.json — добавляет новые autoApprove-инструменты
    4. Обновляет .github/copilot-instructions.md — добавляет секцию skills
    5. Обновляет зависимости (pip)
    6. Показывает changelog (что нового)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path


TEAM_DIR = Path(__file__).resolve().parent.parent  # ai_agents_team/

# Актуальный список autoApprove (все текущие инструменты)
LATEST_AUTO_APPROVE = [
    "create_task",
    "assign_to_department",
    "complete_department_task",
    "handoff",
    "get_task_status",
    "get_task_timeline",
    "list_active_tasks",
    "log_event",
    "escalate",
    "list_skills",
    "get_skill",
    "list_profiles",
    "get_profile",
    "assign_skills_to_agent",
    "get_project_config",
    "set_project_config",
]

CHANGELOG = """
== Что нового в версии 2.0 (библиотека скилов) ==

📚 Новая система управления скилами:
   • 21 встроенный скил по 13 отделам
   • 10 профилей агентов (наборы скилов под роли)
   • Per-project конфигурация (разные скилы для разных проектов)
   • Поддержка внешних скилов (community)

🔌 7 новых MCP-инструментов:
   • list_skills, get_skill — работа со скилами
   • list_profiles, get_profile — профили агентов
   • assign_skills_to_agent — назначение скилов
   • get_project_config, set_project_config — конфиги проектов

📊 Дашборд:
   • Новая секция «Библиотека скилов»
   • Статистика по грейдам и отделам

🧠 Память:
   • Автоматическое сопоставление технологий задачи со скилами

Подробнее: python team.py skills list
"""


def _print_step(emoji: str, message: str):
    print(f"  {emoji} {message}")


def _find_team_in_project(target: Path) -> tuple[Path | None, str]:
    """Находит ai_agents_team в целевом проекте.

    Returns:
        (путь_к_ai_agents_team, тип_подключения)
        Типы: 'submodule', 'copy', 'symlink', None
    """
    candidates = [
        target / "ai_agents_team",
        target.parent / "ai_agents_team",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue

        # Проверка: symlink?
        if candidate.is_symlink():
            return candidate.resolve(), "symlink"

        # Проверка: git submodule?
        gitmodules = target / ".gitmodules"
        if gitmodules.exists():
            try:
                content = gitmodules.read_text(encoding="utf-8")
                if "ai_agents_team" in content:
                    return candidate, "submodule"
            except Exception:
                pass

        # Проверка: .git внутри (отдельный репозиторий)
        if (candidate / ".git").exists() or (candidate / ".git").is_file():
            return candidate, "git"

        # Иначе — копия
        if (candidate / "team.py").exists():
            return candidate, "copy"

    return None, "not_found"


def _update_submodule(target: Path, team_path: Path, dry_run: bool = False) -> bool:
    """Обновляет ai_agents_team через git submodule."""
    _print_step("🔄", "Обновление git submodule...")
    if dry_run:
        _print_step("🔍", "[dry-run] git submodule update --remote ai_agents_team")
        return True

    try:
        result = subprocess.run(
            ["git", "submodule", "update", "--remote", "--init", str(team_path.name)],
            cwd=target,
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            _print_step("✅", "Submodule обновлён")
            return True
        else:
            _print_step("⚠️", f"Не удалось обновить submodule: {result.stderr[:200]}")
            return False
    except Exception as e:
        _print_step("❌", f"Ошибка: {e}")
        return False


def _update_git_repo(team_path: Path, dry_run: bool = False) -> bool:
    """Обновляет ai_agents_team через git pull."""
    _print_step("🔄", "Обновление через git pull...")
    if dry_run:
        _print_step("🔍", f"[dry-run] git pull в {team_path}")
        return True

    try:
        # stash локальных изменений, если есть
        subprocess.run(["git", "stash"], cwd=team_path, capture_output=True, timeout=30)
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=team_path,
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            _print_step("✅", "Репозиторий обновлён")
            return True
        else:
            _print_step("⚠️", f"git pull: {result.stderr[:200]}")
            return False
    except Exception as e:
        _print_step("❌", f"Ошибка: {e}")
        return False


def _update_copy(team_path: Path, dry_run: bool = False) -> bool:
    """Обновляет копию ai_agents_team — копирует только новые/изменённые файлы."""
    _print_step("🔄", "Обновление копии ai_agents_team...")
    if dry_run:
        _print_step("🔍", "[dry-run] копирование skills/ и mcp-server/")
        return True

    try:
        # Копируем skills/ — всю библиотеку скилов
        src_skills = TEAM_DIR / "skills"
        dst_skills = team_path / "skills"
        if src_skills.exists():
            if dst_skills.exists():
                shutil.rmtree(dst_skills)
            shutil.copytree(src_skills, dst_skills)
            _print_step("✅", "skills/ — обновлена библиотека скилов")

        # Копируем обновлённый server.py
        src_server = TEAM_DIR / "mcp-server" / "server.py"
        dst_server = team_path / "mcp-server" / "server.py"
        if src_server.exists():
            shutil.copy2(src_server, dst_server)
            _print_step("✅", "mcp-server/server.py — обновлён")

        # Копируем task_store.py
        src_store = TEAM_DIR / "mcp-server" / "task_store.py"
        dst_store = team_path / "mcp-server" / "task_store.py"
        if src_store.exists():
            shutil.copy2(src_store, dst_store)
            _print_step("✅", "mcp-server/task_store.py — обновлён")

        # Копируем memory/
        src_memory = TEAM_DIR / "memory"
        dst_memory = team_path / "memory"
        if src_memory.exists():
            if dst_memory.exists():
                shutil.rmtree(dst_memory)
            shutil.copytree(src_memory, dst_memory)
            _print_step("✅", "memory/ — обновлена")

        # Копируем dashboard/
        src_dash = TEAM_DIR / "dashboard"
        dst_dash = team_path / "dashboard"
        if src_dash.exists():
            if dst_dash.exists():
                shutil.rmtree(dst_dash)
            shutil.copytree(src_dash, dst_dash)
            _print_step("✅", "dashboard/ — обновлён")

        # Копируем team.py
        shutil.copy2(TEAM_DIR / "team.py", team_path / "team.py")
        _print_step("✅", "team.py — обновлён")

        # Копируем setup.py
        shutil.copy2(TEAM_DIR / "setup.py", team_path / "setup.py")
        _print_step("✅", "setup.py — обновлён")

        # Копируем orchestrator.agent.md
        src_agent = TEAM_DIR / "integration" / "orchestrator.agent.md"
        if src_agent.exists():
            shutil.copy2(src_agent, team_path / "integration" / "orchestrator.agent.md")
            _print_step("✅", "orchestrator.agent.md — обновлён")

        return True

    except Exception as e:
        _print_step("❌", f"Ошибка при копировании: {e}")
        return False


def _update_mcp_config(target: Path, dry_run: bool = False) -> bool:
    """Обновляет .vscode/mcp.json — добавляет новые autoApprove."""
    mcp_file = target / ".vscode" / "mcp.json"
    if not mcp_file.exists():
        _print_step("ℹ️", "MCP-конфиг не найден — создаю новый")
        if dry_run:
            return True
        mcp_file.parent.mkdir(parents=True, exist_ok=True)
        mcp_file.write_text(
            json.dumps({
                "servers": {
                    "ai-agents-coordinator": {
                        "type": "stdio",
                        "command": "python",
                        "args": ["${workspaceFolder}/ai_agents_team/mcp-server/server.py"],
                        "description": "🧠 Координатор AI-команды: задачи, скилы, handoff",
                        "autoApprove": LATEST_AUTO_APPROVE,
                    }
                }
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _print_step("✅", "MCP-конфиг создан с новыми инструментами")
        return True

    if dry_run:
        _print_step("🔍", "[dry-run] Обновление autoApprove в mcp.json")
        return True

    try:
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
        server = config.get("servers", {}).get("ai-agents-coordinator", {})
        current_approve = set(server.get("autoApprove", []))
        new_tools = [t for t in LATEST_AUTO_APPROVE if t not in current_approve]

        if new_tools:
            server["autoApprove"] = list(current_approve | set(LATEST_AUTO_APPROVE))
            # Обновляем описание
            server["description"] = "🧠 Координатор AI-команды: задачи, скилы, handoff"
            mcp_file.write_text(
                json.dumps(config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            _print_step("✅", f"MCP-конфиг обновлён: добавлено {len(new_tools)} инструментов")
            for t in new_tools:
                _print_step("   +", t)
        else:
            _print_step("✅", "MCP-конфиг уже актуален")
        return True
    except Exception as e:
        _print_step("❌", f"Ошибка обновления MCP-конфига: {e}")
        return False


def _update_instructions(target: Path, dry_run: bool = False) -> bool:
    """Обновляет .github/copilot-instructions.md — добавляет секцию skills."""
    instr_file = target / ".github" / "copilot-instructions.md"
    if not instr_file.exists():
        return True  # Не наша инструкция — пропускаем

    if dry_run:
        _print_step("🔍", "[dry-run] Обновление copilot-instructions.md")
        return True

    try:
        content = instr_file.read_text(encoding="utf-8")

        # Добавляем секцию skills, если её нет
        if "## 📚 Библиотека скилов" not in content and "## Skills" not in content:
            skills_section = """
## 📚 Библиотека скилов

Команда имеет собственную библиотеку навыков в `ai_agents_team/skills/`:
- `python team.py skills list` — список всех скилов
- `python team.py skills profiles` — профили агентов
- `python team.py skills active <project>` — активные скилы проекта
- `python skills/loader.py install <url>` — подключить внешние скилы
"""
            instr_file.write_text(content + skills_section, encoding="utf-8")
            _print_step("✅", "copilot-instructions.md — добавлена секция skills")
        else:
            _print_step("✅", "copilot-instructions.md уже содержит секцию skills")

        return True
    except Exception as e:
        _print_step("❌", f"Ошибка обновления инструкций: {e}")
        return False


def _install_dependencies(target: Path, dry_run: bool = False) -> bool:
    """Обновляет зависимости pip."""
    _print_step("📦", "Проверка зависимостей...")
    if dry_run:
        _print_step("🔍", "[dry-run] pip install -r mcp-server/requirements.txt")
        return True

    # Ищем venv в целевом проекте
    pip_cmd = [sys.executable, "-m", "pip"]
    for venv_name in (".venv", "venv", ".env", "env"):
        for py in ["Scripts/python.exe", "bin/python"]:
            candidate = target / venv_name / py
            if candidate.exists():
                pip_cmd = [str(candidate), "-m", "pip"]
                break

    # Устанавливаем зависимости MCP-сервера
    req_file = TEAM_DIR / "mcp-server" / "requirements.txt"
    if req_file.exists():
        try:
            subprocess.run(
                [*pip_cmd, "install", "--yes", "-r", str(req_file)],
                capture_output=True, text=True, check=False, timeout=60,
            )
            _print_step("✅", "Зависимости MCP-сервера обновлены")
        except Exception as e:
            _print_step("⚠️", f"pip install: {e}")

    # Устанавливаем пакет ai-devcorp (editable)
    try:
        subprocess.run(
            [*pip_cmd, "install", "--yes", "-e", str(TEAM_DIR)],
            capture_output=True, text=True, check=False, timeout=60,
        )
        _print_step("✅", "Пакет ai-devcorp обновлён")
    except Exception as e:
        _print_step("⚠️", f"pip install -e: {e}")

    return True


def update(target_path: str, dry_run: bool = False):
    """Запустить процесс обновления."""
    target = Path(target_path).resolve()

    if not target.exists() or not target.is_dir():
        print(f"❌ Целевой путь не существует или не директория: {target}")
        sys.exit(1)

    print()
    print("=" * 60)
    print(f"  🔄 AI DevCorp — Обновление")
    print(f"  Цель: {target}")
    if dry_run:
        print(f"  Режим: 🔍 ПРОВЕРКА (dry-run)")
    print("=" * 60)
    print()

    # Шаг 1: Найти ai_agents_team
    _print_step("🔍", "Поиск ai_agents_team в проекте...")
    team_path, connection_type = _find_team_in_project(target)

    if connection_type == "not_found":
        _print_step("❌", "ai_agents_team не найден в целевом проекте!")
        _print_step("💡", "Проверьте: ai_agents_team/ должен быть в корне проекта")
        _print_step("💡", "Или выполните первую интеграцию: python integrate.py <target>")
        sys.exit(1)

    _print_step("✅", f"ai_agents_team найден: {team_path} (тип: {connection_type})")
    print()

    # Шаг 2: Обновить ai_agents_team
    print("  ── Шаг 1: Обновление ai_agents_team ──")
    if connection_type == "submodule":
        ok = _update_submodule(target, team_path, dry_run)
    elif connection_type == "git":
        ok = _update_git_repo(team_path, dry_run)
    elif connection_type == "symlink":
        _print_step("ℹ️", "Симлинк — обновление не требуется (исходный репозиторий)")
        ok = True
    else:  # copy
        ok = _update_copy(team_path, dry_run)

    if not ok:
        print("\n⚠️  Обновление ai_agents_team прервано")
        sys.exit(1)
    print()

    # Шаг 3: Обновить MCP-конфиг
    print("  ── Шаг 2: MCP-конфиг ──")
    _update_mcp_config(target, dry_run)
    print()

    # Шаг 4: Обновить инструкции Copilot
    print("  ── Шаг 3: Инструкции Copilot ──")
    _update_instructions(target, dry_run)
    print()

    # Шаг 5: Обновить зависимости
    print("  ── Шаг 4: Зависимости ──")
    _install_dependencies(target, dry_run)
    print()

    # Финальный отчёт
    print("=" * 60)
    print(f"  {'✅' if not dry_run else '🔍'} Обновление завершено!")
    print("=" * 60)

    if dry_run:
        print("\n  🔍 Это был проверочный запуск. Никаких изменений не внесено.")
        print("  ▶️  Запустите без --dry-run для применения:")
        print(f"     python {sys.argv[0]} {target_path}")
    else:
        print(CHANGELOG)
        print()
        _print_step("💡", "Перезагрузите окно VS Code (Ctrl+Shift+P → Reload Window)")
        _print_step("💡", "Новые MCP-инструменты станут доступны сразу")
        _print_step("💡", "Проверьте: python team.py skills list")

    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        print()
        print("Примеры:")
        print(f"  python {sys.argv[0]} /path/to/my-project")
        print(f"  python {sys.argv[0]} /path/to/my-project --dry-run")
        sys.exit(0)

    dry_run = "--dry-run" in sys.argv
    target = sys.argv[1] if sys.argv[1] != "--dry-run" else sys.argv[2] if len(sys.argv) > 2 else "."

    update(target, dry_run)


if __name__ == "__main__":
    main()
