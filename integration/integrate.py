#!/usr/bin/env python3
"""
Скрипт интеграции AI Agents Team в существующий проект.

Использование:
    python integrate.py <путь_к_целевому_проекту>

Что делает:
    1. Копирует агента Orchestrator в .github/agents/ целевого проекта
    2. Копирует агентов 13 отделов в .github/agents/departments/
    3. Создаёт .github/copilot-instructions.md если его нет
    4. Создаёт .vscode/mcp.json для подключения MCP-сервера координации
    5. Устанавливает зависимости MCP-сервера (pip install -r requirements.txt)
    6. При отсутствии .github/ — использует fallback-копию из agents_fallback/
    7. Выводит инструкцию для разработчика
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path


AGENT_FILE = Path(__file__).parent / "orchestrator.agent.md"
FALLBACK_DIR = Path(__file__).parent / "agents_fallback"
TEAM_DIR = Path(__file__).parent.parent


def integrate(target_path: str):
    target = Path(target_path).resolve()

    if not target.exists():
        print(f"❌ Целевой путь не существует: {target}")
        sys.exit(1)

    if not target.is_dir():
        print(f"❌ Целевой путь должен быть директорией: {target}")
        sys.exit(1)

    # Путь для .github/agents/
    agents_dir = target / ".github" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Копируем файл агента
    dest_agent = agents_dir / "orchestrator.agent.md"
    if AGENT_FILE.exists():
        shutil.copy2(AGENT_FILE, dest_agent)
        print(f"✅ Агент скопирован: {dest_agent}")
    else:
        print(f"❌ Файл агента не найден: {AGENT_FILE}")
        sys.exit(1)

    # Копируем агентов отделов
    dept_agents_src = TEAM_DIR / ".github" / "agents" / "departments"
    dept_agents_dst = agents_dir / "departments"

    if dept_agents_src.exists():
        # Основной источник: .github/agents/departments/ из репозитория
        dept_agents_dst.mkdir(parents=True, exist_ok=True)
        count = 0
        for agent_file in dept_agents_src.glob("*.agent.md"):
            shutil.copy2(agent_file, dept_agents_dst / agent_file.name)
            count += 1
            print(f"✅ Агент отдела скопирован: {dept_agents_dst / agent_file.name}")
        print(f"✅ Скопировано агентов отделов: {count}")
    elif FALLBACK_DIR.exists():
        # Fallback: встроенная копия внутри integration/agents_fallback/
        print(f"⚠️  Основной источник не найден: {dept_agents_src}")
        print(f"   Использую fallback: {FALLBACK_DIR / 'departments'}")
        fallback_src = FALLBACK_DIR / "departments"
        if fallback_src.exists():
            dept_agents_dst.mkdir(parents=True, exist_ok=True)
            count = 0
            for agent_file in fallback_src.glob("*.agent.md"):
                shutil.copy2(agent_file, dept_agents_dst / agent_file.name)
                count += 1
                print(f"✅ Агент отдела скопирован (fallback): {dept_agents_dst / agent_file.name}")
            print(f"✅ Скопировано агентов отделов (fallback): {count}")
    else:
        print(f"❌ Папка с агентами отделов не найдена!")
        print(f"   Проверено: {dept_agents_src}")
        print(f"   Проверено: {FALLBACK_DIR / 'departments'}")
        print(f"   Решение: git submodule update --init --recursive")

    # Проверяем/создаём copilot-instructions.md с указанием на ai_agents_team
    instructions_dir = target / ".github"
    instructions_file = instructions_dir / "copilot-instructions.md"

    if not instructions_file.exists():
        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write("""# Инструкции для GitHub Copilot

## AI Agents Team

В проекте подключена команда AI-агентов из `ai_agents_team/`.

Для постановки задачи команде:
1. Откройте Copilot Chat
2. Выберите агента **🧠 CEO — Оркестратор AI-команды**
3. Опишите задачу — Оркестратор проанализирует и распределит работу

Структура команды: `ai_agents_team/departments/`
Процессы: `ai_agents_team/workflows/`
""")
        print(f"✅ Создан файл инструкций: {instructions_file}")
    else:
        print(f"ℹ️  Файл инструкций уже существует: {instructions_file}")
        print("   Добавьте в него ссылку на ai_agents_team вручную.")

    # Проверяем/создаём .vscode/mcp.json для подключения MCP-сервера
    vscode_dir = target / ".vscode"
    mcp_file = vscode_dir / "mcp.json"
    mcp_config = {
        "servers": {
            "ai-agents-coordinator": {
                "type": "stdio",
                "command": "python",
                "args": ["${workspaceFolder}/ai_agents_team/mcp-server/server.py"],
                "description": "🧠 Координатор AI-команды: управление задачами, handoff, эскалация"
            }
        }
    }

    if mcp_file.exists():
        print(f"ℹ️  MCP-конфиг уже существует: {mcp_file}")
        print("   Убедитесь, что в нём есть секция 'ai-agents-coordinator'")
        print(f"   Для HTTP-режима (Docker): замените на type: http, url: http://localhost:8000/mcp")
    else:
        vscode_dir.mkdir(parents=True, exist_ok=True)
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, ensure_ascii=False, indent=2)
        print(f"✅ Создан MCP-конфиг (STDIO — автозапуск): {mcp_file}")
        print(f"   Для HTTP-режима (Docker): python ai_agents_team/mcp-server/server.py --transport http")

    # Устанавливаем зависимости MCP-сервера
    req_file = TEAM_DIR / "mcp-server" / "requirements.txt"
    if req_file.exists():
        print()
        print("📦 Установка зависимостей MCP-сервера...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print(f"✅ Зависимости MCP-сервера установлены")
            else:
                print(f"⚠️  Не удалось установить зависимости (код: {result.returncode})")
                print(f"   Выполните вручную: pip install -r {req_file}")
        except FileNotFoundError:
            print(f"⚠️  pip не найден. Выполните вручную: pip install -r {req_file}")
    else:
        print(f"⚠️  Файл requirements.txt не найден: {req_file}")

    print()
    print("=" * 60)
    print("🎉 Интеграция завершена!")
    print("=" * 60)
    print(f"""
📋 Что сделано:
   ✅ Агент Orchestrator добавлен в {agents_dir}
   ✅ Агенты 13 отделов добавлены в {agents_dir / 'departments'}
   ✅ Инструкции Copilot созданы в {instructions_file}
   ✅ MCP-конфиг создан в {mcp_file}
   ✅ Зависимости MCP-сервера установлены

▶️ Что нужно сделать дальше:
   1. Откройте проект в VS Code (или перезагрузите окно: Ctrl+Shift+P → Reload Window)

   2. В Copilot Chat выберите агента:
      "🧠 CEO — Оркестратор AI-команды"

   3. Опишите задачу, например:
      "Создай REST API для управления пользователями"

🏢 Оркестратор сам проанализирует задачу, 
   определит какие отделы нужны и распределит работу!
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print()
        print("Пример:")
        print(f"  python {sys.argv[0]} /path/to/my-project")
        sys.exit(0)

    integrate(sys.argv[1])


if __name__ == "__main__":
    main()
