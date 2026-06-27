#!/usr/bin/env python3
"""
Скрипт интеграции AI Agents Team в существующий проект.

Использование:
    python integrate.py <путь_к_целевому_проекту>

Что делает:
    1. Копирует агента Orchestrator в .github/agents/ целевого проекта
    2. Создаёт .github/copilot-instructions.md если его нет
    3. Выводит инструкцию для разработчика
"""

import sys
import shutil
from pathlib import Path


AGENT_FILE = Path(__file__).parent / "orchestrator.agent.md"
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

    print()
    print("=" * 60)
    print("🎉 Интеграция завершена!")
    print("=" * 60)
    print(f"""
📋 Что сделано:
   ✅ Агент Orchestrator добавлен в {agents_dir}
   ✅ Инструкции созданы в {instructions_file}

▶️ Что нужно сделать дальше:
   1. Убедитесь, что ai_agents_team находится в корне проекта:
      {target / 'ai_agents_team'}
      (склонируйте или добавьте как submodule, если ещё нет)

   2. Откройте проект в VS Code

   3. В Copilot Chat выберите агента:
      "🧠 CEO — Оркестратор AI-команды"

   4. Опишите задачу, например:
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
